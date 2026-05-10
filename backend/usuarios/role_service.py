"""
RoleService — business logic for RBAC role assignment.

Pattern: Service layer owns business rules; delegates persistence to UoW/repositories.

Exported functions:
  get_user_roles(uow, user_id) -> list[UsuarioRol]
  assign_role(uow, user_id, rol_nombre) -> AssignRoleResponse
  remove_role(uow, user_id, rol_nombre) -> None
"""
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from core.models import Rol, Usuario, UsuarioRol
from infrastructure.uow import UnitOfWork
from usuarios.role_schemas import AssignRoleResponse


class RoleService:
    """
    Service for managing RBAC role assignments.

    All methods accept a UoW instance. The caller is responsible for wrapping
    calls in an ``async with uow:`` context manager for atomicity.
    """

    @staticmethod
    async def get_user_roles(uow: UnitOfWork, user_id: int) -> list[UsuarioRol]:
        """
        Return all UsuarioRol pivot records for a user.

        Uses explicit selectinload to avoid lazy-load errors in AsyncSession.

        Args:
            uow: Active Unit of Work (session must be open).
            user_id: Primary key of the user.

        Returns:
            List of UsuarioRol records (may be empty).
        """
        stmt = (
            select(Usuario)
            .where(Usuario.id == user_id)
            .options(selectinload(Usuario.roles))
        )
        result = await uow.session.execute(stmt)
        usuario = result.scalar_one_or_none()
        if usuario is None:
            return []

        # Build UsuarioRol pivot list from eager-loaded roles
        usuario_roles = []
        for rol in usuario.roles:
            ur = UsuarioRol(usuario_id=user_id, rol_id=rol.id)
            usuario_roles.append(ur)
        return usuario_roles

    @staticmethod
    async def assign_role(
        uow: UnitOfWork, user_id: int, rol_nombre: str
    ) -> AssignRoleResponse:
        """
        Assign a new role to a user, replacing all existing roles.

        Business rules enforced:
        1. User must exist (HTTP 404 if not).
        2. Role must exist in DB (HTTP 422 if not).
        3. "Last admin" protection: if the user currently has ADMIN and the new
           role is different, at least one other active ADMIN must remain
           (HTTP 409 if not).
        4. Idempotent: assigning the same role the user already has is a no-op.

        Uses datetime.utcnow() (NOT datetime.now(UTC)) for timestamps.

        Args:
            uow: Active Unit of Work.
            user_id: Primary key of the user to modify.
            rol_nombre: Name of the role to assign (already validated/uppercased).

        Returns:
            AssignRoleResponse with user_id, rol_nombre, and a confirmation message.

        Raises:
            HTTPException 404 — user not found.
            HTTPException 409 — would remove the last ADMIN.
            HTTPException 422 — role not found in DB.
        """
        # 1. Verify user exists (with roles eagerly loaded)
        stmt = (
            select(Usuario)
            .where(Usuario.id == user_id)
            .where(Usuario.eliminado_en.is_(None))
            .options(selectinload(Usuario.roles))
        )
        result = await uow.session.execute(stmt)
        usuario = result.scalar_one_or_none()

        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "type": "https://tools.ietf.org/html/rfc7807",
                    "title": "User Not Found",
                    "detail": f"User with id={user_id} does not exist or has been deleted.",
                    "status": 404,
                },
            )

        # 2. Verify the target role exists in DB
        target_rol = await uow.roles.find_by(nombre=rol_nombre)
        if target_rol is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "https://tools.ietf.org/html/rfc7807",
                    "title": "Invalid Role",
                    "detail": f"Role '{rol_nombre}' does not exist in the database.",
                    "status": 422,
                },
            )

        # 3. "Last admin" protection
        current_role_names = {rol.nombre for rol in usuario.roles}
        is_currently_admin = "ADMIN" in current_role_names

        if is_currently_admin and rol_nombre != "ADMIN":
            # Count other active admins (SELECT FOR UPDATE via with_for_update)
            admin_rol_stmt = select(Rol).where(Rol.nombre == "ADMIN")
            admin_rol_result = await uow.session.execute(admin_rol_stmt)
            admin_rol = admin_rol_result.scalar_one_or_none()

            if admin_rol is not None:
                # Lock rows first, then count — PostgreSQL doesn't allow FOR UPDATE with COUNT
                lock_stmt = (
                    select(UsuarioRol.usuario_id)
                    .where(UsuarioRol.rol_id == admin_rol.id)
                    .with_for_update()
                )
                lock_result = await uow.session.execute(lock_stmt)
                admin_count = len(lock_result.scalars().all())

                if admin_count <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "type": "https://tools.ietf.org/html/rfc7807",
                            "title": "Last Admin Protection",
                            "detail": "Cannot remove the last admin. "
                                      "Assign ADMIN to another user first.",
                            "status": 409,
                        },
                    )

        # 4. Idempotency check: already has the target role and only that role
        if current_role_names == {rol_nombre}:
            return AssignRoleResponse(
                user_id=user_id,
                rol_nombre=rol_nombre,
                mensaje=f"User {user_id} already has role {rol_nombre}. No change needed.",
            )

        # 5. Remove all current roles for this user (clean slate)
        existing_pivot_records = await uow.usuario_roles.find_all_by(usuario_id=user_id)
        for pivot in existing_pivot_records:
            await uow.session.delete(pivot)
        await uow.session.flush()

        # 6. Assign the new role
        nuevo_pivot = UsuarioRol(
            usuario_id=user_id,
            rol_id=target_rol.id,
        )
        await uow.usuario_roles.create(nuevo_pivot)

        return AssignRoleResponse(
            user_id=user_id,
            rol_nombre=rol_nombre,
            mensaje=f"Role {rol_nombre} successfully assigned to user {user_id}.",
        )

    @staticmethod
    async def remove_role(uow: UnitOfWork, user_id: int, rol_nombre: str) -> None:
        """
        Remove a specific role from a user (idempotent).

        If the user does not have the specified role, the operation silently
        succeeds (no error raised).

        Args:
            uow: Active Unit of Work.
            user_id: Primary key of the user.
            rol_nombre: Name of the role to remove.
        """
        # Find the role record
        rol = await uow.roles.find_by(nombre=rol_nombre)
        if rol is None:
            # Role doesn't exist in DB — nothing to remove
            return

        # Find the pivot record
        pivot = await uow.usuario_roles.find_by(
            usuario_id=user_id, rol_id=rol.id
        )
        if pivot is None:
            # User doesn't have this role — idempotent, do nothing
            return

        await uow.session.delete(pivot)
        await uow.session.flush()
