import json
import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import DatabaseError, models, router
from django.db.models import Q


class CompatibleArrayField(ArrayField):
    """ArrayField compatível com PostgreSQL (nativo array) e SQLite (fallback JSON texto)."""

    def db_type(self, connection):
        if connection.vendor == "sqlite":
            return "text"
        return super().db_type(connection)

    def get_placeholder(self, value, compiler, connection):
        if connection.vendor == "sqlite":
            return "%s"
        return super().get_placeholder(value, compiler, connection)

    def get_db_prep_save(self, value, connection):
        if connection.vendor == "sqlite":
            if value is None:
                return None
            return json.dumps([str(v) if isinstance(v, uuid.UUID) else v for v in value])
        return super().get_db_prep_save(value, connection)

    def from_db_value(self, value, expression, connection):
        if connection.vendor == "sqlite" and isinstance(value, str):
            raw_list = json.loads(value)
            if isinstance(self.base_field, models.UUIDField):
                return [uuid.UUID(v) if isinstance(v, str) else v for v in raw_list]
            return raw_list
        return value


class CompositeKeyForeignKey(models.ForeignKey):
    """
    ForeignKey que atua como coluna líder de chave primária composta em tabelas
    associativas do SOSP (catalogServiceAgency, catalogUnitService) no Django 5.1.

    Nota Arquitetural (Django 5.1 vs Django 5.2+):
    O Django 5.1.15 não possui `models.CompositePrimaryKey` nativo (introduzido no Django 5.2).
    Para evitar a criação de uma coluna artificial `id` inexistente no schema físico
    PostgreSQL (`baseline_0001_schema.sql`), a primeira coluna da chave composta recebe
    `primary_key=True` e o model herda obrigatoriamente de `CompositeKeyModel`, que
    impõe semântica estrita de chave composta `(col1, col2)` nas operações ORM.
    """

    def _check_unique(self, **kwargs):
        composite_fields = getattr(self.model, "_composite_key_fields", None)
        unique_together = [tuple(ut) for ut in getattr(self.model._meta, "unique_together", ())]
        if (
            composite_fields
            and len(composite_fields) == 2
            and self.name in composite_fields
            and tuple(composite_fields) in unique_together
        ):
            return []
        return super()._check_unique(**kwargs)


class CompositeKeyQuerySet(models.QuerySet):
    """
    QuerySet seguro para models com chave primária composta de 2 colunas no Django 5.1.
    Garante que filtros, deleções e `update_or_create`/`get_or_create` operem
    estritamente sobre o par `(col1, col2)` e bloqueia usos ambíguos de `pk` escalar.
    """

    def _get_composite_fields(self) -> tuple[str, str]:
        fields = getattr(self.model, "_composite_key_fields", ())
        if len(fields) != 2:
            raise ValueError(
                f"{self.model.__name__} deve definir `_composite_key_fields = (col1, col2)`."
            )
        return fields

    def _expand_pk_tuple(self, value) -> dict:
        k1, k2 = self._get_composite_fields()
        if isinstance(value, (tuple, list)) and len(value) == 2:
            v1, v2 = value
            key1 = k1 if isinstance(v1, models.Model) else f"{k1}_id"
            key2 = k2 if isinstance(v2, models.Model) else f"{k2}_id"
            return {key1: v1, key2: v2}
        raise ValueError(
            f"Operação por 'pk' escalar é proibida em {self.model.__name__} "
            f"(chave primária composta ({k1}, {k2}) no Django 5.1). "
            f"Utilize filtro explícito pelas duas colunas ({k1}=..., {k2}=...) "
            f"ou a tupla pk=({k1}_id, {k2}_id)."
        )

    def _normalize_q(self, q_obj: Q) -> Q:
        k1, k2 = self._get_composite_fields()
        new_children = []
        for child in q_obj.children:
            if isinstance(child, Q):
                new_children.append(self._normalize_q(child))
            elif isinstance(child, tuple) and len(child) == 2:
                lookup, val = child
                if lookup in ("pk", "pk__exact"):
                    expanded = self._expand_pk_tuple(val)
                    new_children.append(Q(**expanded))
                elif lookup.startswith("pk__"):
                    raise ValueError(
                        f"Lookup '{lookup}' não é suportado em {self.model.__name__} "
                        f"(chave primária composta ({k1}, {k2}))."
                    )
                else:
                    new_children.append(child)
            else:
                new_children.append(child)
        cloned = Q(*new_children)
        cloned.connector = q_obj.connector
        cloned.negated = q_obj.negated
        return cloned

    def _normalize_composite_pk_lookups(self, args, kwargs):
        k1, k2 = self._get_composite_fields()
        norm_args = tuple(self._normalize_q(a) if isinstance(a, Q) else a for a in args)
        norm_kwargs = dict(kwargs)
        for key in list(norm_kwargs.keys()):
            if key in ("pk", "pk__exact"):
                val = norm_kwargs.pop(key)
                norm_kwargs.update(self._expand_pk_tuple(val))
            elif key.startswith("pk__"):
                raise ValueError(
                    f"Lookup '{key}' não é suportado em {self.model.__name__} "
                    f"(chave primária composta ({k1}, {k2}))."
                )
        return norm_args, norm_kwargs

    def filter(self, *args, **kwargs):
        norm_args, norm_kwargs = self._normalize_composite_pk_lookups(args, kwargs)
        return super().filter(*norm_args, **norm_kwargs)

    def exclude(self, *args, **kwargs):
        norm_args, norm_kwargs = self._normalize_composite_pk_lookups(args, kwargs)
        return super().exclude(*norm_args, **norm_kwargs)

    def get(self, *args, **kwargs):
        norm_args, norm_kwargs = self._normalize_composite_pk_lookups(args, kwargs)
        return super().get(*norm_args, **norm_kwargs)

    def _validate_full_composite_key_in_kwargs(self, kwargs: dict, method_name: str):
        k1, k2 = self._get_composite_fields()
        has_k1 = k1 in kwargs or f"{k1}_id" in kwargs
        has_k2 = k2 in kwargs or f"{k2}_id" in kwargs
        if not (has_k1 and has_k2):
            raise ValueError(
                f"{self.model.__name__}.{method_name}() exige ambas as colunas da chave "
                f"composta ('{k1}' e '{k2}'). Recebido: {sorted(kwargs.keys())}."
            )

    def get_or_create(self, defaults=None, **kwargs):
        _, norm_kwargs = self._normalize_composite_pk_lookups((), kwargs)
        self._validate_full_composite_key_in_kwargs(norm_kwargs, "get_or_create")
        return super().get_or_create(defaults=defaults, **norm_kwargs)

    def update_or_create(self, defaults=None, create_defaults=None, **kwargs):
        _, norm_kwargs = self._normalize_composite_pk_lookups((), kwargs)
        self._validate_full_composite_key_in_kwargs(norm_kwargs, "update_or_create")
        return super().update_or_create(
            defaults=defaults,
            create_defaults=create_defaults,
            **norm_kwargs,
        )

    def delete(self):
        """
        Executa deleção SQL direta (`_raw_delete`) preservando o predicado WHERE completo,
        jamais agrupando pela primeira coluna isolada (`instance.pk`).
        """
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with delete()."
        del_query = self._chain()
        del_query._for_write = True
        del_query.query.select_for_update = False
        del_query.query.select_related = False
        del_query.query.clear_ordering(force=True)
        deleted_count = del_query._raw_delete(using=del_query.db)
        return deleted_count, {self.model._meta.label: deleted_count}

    def in_bulk(self, id_list=None, *, field_name="pk"):
        raise ValueError(
            f"in_bulk() não é suportado em {self.model.__name__} no Django 5.1 "
            "por possuir chave primária composta."
        )

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValueError(
            f"bulk_update() não é suportado em {self.model.__name__} no Django 5.1 "
            "por possuir chave primária composta. Utilize filter(...).update(...) ou update_or_create()."
        )


class CompositeKeyModel(models.Model):
    """
    Model abstrato para tabelas associativas com chave primária composta de 2 colunas
    no SOSP (`catalogServiceAgency` e `catalogUnitService`) sob Django 5.1.15.
    """

    _composite_key_fields: tuple[str, str] = ()

    objects = CompositeKeyQuerySet.as_manager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loaded_composite_key = None

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._loaded_composite_key = instance.composite_pk
        return instance

    @property
    def composite_pk(self) -> tuple:
        k1, k2 = self._composite_key_fields
        return (getattr(self, f"{k1}_id", None), getattr(self, f"{k2}_id", None))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.composite_pk[0] is None or self.composite_pk[1] is None:
            return self is other
        return self.composite_pk == other.composite_pk

    def __hash__(self):
        if self.composite_pk[0] is None or self.composite_pk[1] is None:
            raise TypeError("Model instances without composite primary key value are unhashable")
        return hash((self.__class__, self.composite_pk))

    def save(self, *args, **kwargs):
        k1, k2 = self._composite_key_fields
        v1, v2 = self.composite_pk
        if v1 is None or v2 is None:
            raise ValueError(
                f"{self.__class__.__name__}.save() exige ambas as colunas da chave composta ({k1}_id, {k2}_id)."
            )

        if self._state.adding or kwargs.get("force_insert"):
            kwargs["force_insert"] = True
            result = super().save(*args, **kwargs)
            self._loaded_composite_key = self.composite_pk
            return result

        if self._loaded_composite_key is not None and self.composite_pk != self._loaded_composite_key:
            raise ValueError(
                f"Não é permitido alterar colunas da chave primária composta ({k1}, {k2}) "
                f"em uma instância já persistida de {self.__class__.__name__}. "
                "Exclua o vínculo anterior e crie um novo registro."
            )

        using = kwargs.get("using") or router.db_for_write(self.__class__, instance=self)
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            update_fields_set = set(update_fields)
            if k1 in update_fields_set or f"{k1}_id" in update_fields_set or k2 in update_fields_set or f"{k2}_id" in update_fields_set:
                raise ValueError(
                    f"Não é permitido incluir colunas da chave primária composta ({k1}, {k2}) em update_fields."
                )

        non_key_fields = [
            f.attname
            for f in self._meta.local_concrete_fields
            if f.name not in self._composite_key_fields and not getattr(f, "auto_now_add", False)
        ]
        if update_fields is not None:
            allowed = set(update_fields)
            non_key_fields = [
                f.attname
                for f in self._meta.local_concrete_fields
                if (f.name in allowed or f.attname in allowed) and f.name not in self._composite_key_fields
            ]

        qs = type(self).objects.using(using).filter(**{f"{k1}_id": v1, f"{k2}_id": v2})
        if non_key_fields:
            update_payload = {att: getattr(self, att) for att in non_key_fields}
            updated = qs.update(**update_payload)
        else:
            updated = 1 if qs.exists() else 0

        if not updated and kwargs.get("force_update"):
            raise DatabaseError("Forced update did not affect any rows.")

        self._loaded_composite_key = self.composite_pk
        return None

    def delete(self, using=None, keep_parents=False):
        k1, k2 = self._composite_key_fields
        v1, v2 = self.composite_pk
        if v1 is None or v2 is None:
            raise ValueError(
                f"{self.__class__.__name__}.delete() exige ambas as colunas da chave composta ({k1}_id, {k2}_id)."
            )
        if self._loaded_composite_key is not None and self.composite_pk != self._loaded_composite_key:
            raise ValueError(
                f"Não é permitido excluir instância de {self.__class__.__name__} cuja chave composta foi modificada em memória."
            )
        using = using or router.db_for_write(self.__class__, instance=self)
        return type(self).objects.using(using).filter(**{f"{k1}_id": v1, f"{k2}_id": v2}).delete()
