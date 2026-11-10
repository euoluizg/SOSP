"""
SOSP — Permissões Baseadas em Papéis (RBAC - ADR-003, RS-01 a RS-03).

Define classes de permissão do Django REST Framework para:
1. IsCitizen: Acesso exclusivo a cidadãos autenticados.
2. IsServerUser: Acesso a servidores públicos e administradores.
3. IsAdminUser: Acesso exclusivo a administradores e superadministradores.
4. IsInstitutionalUser: Acesso a usuários institucionais (servidores e administradores), bloqueando cidadãos.
"""

from rest_framework.permissions import BasePermission


class IsCitizen(BasePermission):
    """Permite acesso apenas a cidadãos autenticados."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and getattr(request.user, "is_authenticated", False)
            and getattr(request.user, "role", None) in ("citizen", "cidadao")
        )


class HasChangedTemporaryPassword(BasePermission):
    """Bloqueia usuários institucionais que precisam alterar a senha temporária no primeiro acesso."""
    message = "É obrigatório alterar a senha temporária no primeiro acesso antes de realizar operações no sistema."
    code = "CHANGE_PASSWORD_REQUIRED"

    def has_permission(self, request, view):
        return not bool(
            request.user
            and getattr(request.user, "is_authenticated", False)
            and getattr(request.user, "must_change_password", False)
        )


class IsServerUser(BasePermission):
    """Permite acesso a servidores lotados, gestores institucionais e administradores (ADR-003)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and getattr(request.user, "is_authenticated", False)
            and not getattr(request.user, "must_change_password", False)
            and getattr(request.user, "role", None)
            in (
                "server",
                "servant",
                "servidor",
                "gestor",
                "manager",
                "admin",
                "administrator",
                "superadmin",
                "administrador",
            )
        )


class IsManagerUser(BasePermission):
    """Permite acesso exclusivamente a gestores institucionais e administradores (ADR-003)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and getattr(request.user, "is_authenticated", False)
            and not getattr(request.user, "must_change_password", False)
            and getattr(request.user, "role", None)
            in (
                "gestor",
                "manager",
                "admin",
                "administrator",
                "superadmin",
                "administrador",
            )
        )


class IsAdminUser(BasePermission):
    """Permite acesso exclusivamente a administradores e superadministradores."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and getattr(request.user, "is_authenticated", False)
            and not getattr(request.user, "must_change_password", False)
            and getattr(request.user, "role", None)
            in (
                "admin",
                "administrator",
                "superadmin",
                "administrador",
            )
        )


class IsInstitutionalUser(BasePermission):
    """
    Permite acesso a usuários institucionais: servidores, gestores e administradores (ADR-003).
    Bloqueia cidadãos e anônimos (retorna 403 para cidadão autenticado).
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and getattr(request.user, "is_authenticated", False)
            and not getattr(request.user, "must_change_password", False)
            and getattr(request.user, "role", None)
            in (
                "server",
                "servant",
                "servidor",
                "gestor",
                "manager",
                "admin",
                "administrator",
                "superadmin",
                "administrador",
            )
        )
