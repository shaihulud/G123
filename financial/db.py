from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

import sqlalchemy as sa
from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, selectinload, sessionmaker
from sqlalchemy.sql import operators

from financial.config import settings


engine = create_async_engine(
    settings.DB_DSN,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    future=True,
)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession, future=True, autoflush=False)

TBase = TypeVar("TBase", bound="EmptyBaseModel")
metadata = MetaData()
Base = declarative_base(metadata=metadata)


operators_map = {
    "isnull": lambda c, v: (c == None) if v else (c != None),
    "exact": operators.eq,
    "ne": operators.ne,  # not equal or is not (for None)
    "gt": operators.gt,  # greater than , >
    "ge": operators.ge,  # greater than or equal, >=
    "lt": operators.lt,  # lower than, <
    "le": operators.le,  # lower than or equal, <=
    "in": operators.in_op,
    "notin": operators.notin_op,
    "between": lambda c, v: c.between(v[0], v[1]),
    "like": operators.like_op,
    "ilike": operators.ilike_op,
    "startswith": operators.startswith_op,
    "istartswith": lambda c, v: c.ilike(v + "%"),
    "endswith": operators.endswith_op,
    "iendswith": lambda c, v: c.ilike("%" + v),
    "overlaps": lambda c, v: getattr(c, "overlaps")(v),
}


class EmptyBaseModel(Base):  # type: ignore
    """
    Abstract base model for SQLAlchemy models inheritance.
    Contains methods for accessing and filtering in the database.
    """

    __abstract__ = True

    def __str__(self):
        return f"<{type(self).__name__}({self.id=})>"

    @classmethod
    def _get_query(cls: Type[TBase], prefetch: Optional[Tuple[str, ...]] = None) -> Any:
        query = sa.select(cls)
        if prefetch:
            options: List[Any] = [selectinload(x) for x in prefetch]
            query = query.options(*options).execution_options(populate_existing=True)
        return query

    @classmethod
    def _build_sorting(cls: Type[TBase], sorting: Dict[str, str]) -> List[Any]:
        """Builds list of ORDER_BY clauses"""
        result = []
        for field_name, direction in sorting.items():
            field = getattr(cls, field_name)
            result.append(getattr(field, direction)())
        return result

    @classmethod
    def build_filters(cls: Type[TBase], filters: Dict[str, Any]) -> List[Any]:
        """Builds list of WHERE conditions"""
        result = []
        for expression, value in filters.items():
            parts = expression.split("__")
            op_name = parts[1] if len(parts) > 1 else "exact"
            if op_name not in operators_map:
                raise KeyError(f"Expression {expression} has incorrect operator {op_name}")
            operator = operators_map[op_name]
            column = getattr(cls, parts[0])
            result.append(operator(column, value))
        return result

    @classmethod
    async def insert_or_update(
        cls: Type[TBase], db: AsyncSession, ids: Dict[str, Any], values: Dict[str, Any]
    ) -> TBase:
        to_set = {**ids, **values}
        query = insert(cls).values(**to_set)
        query = query.on_conflict_do_update(
            index_elements=ids.keys(),
            set_=to_set,
            where=sa.and_(True, *cls.build_filters(ids)),
        )
        db_execute = await db.execute(query)
        return db_execute.inserted_primary_key[0]

    @classmethod
    async def paginate(
        cls: Type[TBase],
        db: AsyncSession,
        filters: Optional[Dict[str, Any]],
        join: Optional[List[Any]] = None,
        sorting: Optional[Dict[str, str]] = None,
        prefetch: Optional[Tuple[str, ...]] = None,
        page: Optional[int] = 1,
        per_page: Optional[int] = 5,
    ) -> Tuple[List[TBase], int, int]:
        query = cls._get_query(prefetch)

        if join:
            query = query.join(*join)

        if sorting is not None:
            query = query.order_by(*cls._build_sorting(sorting))

        if filters is not None:
            query = query.where(sa.and_(True, *cls.build_filters(filters)))

        total = await db.scalar(sa.select([sa.func.count()]).select_from(query))
        pages = total // per_page if not total % per_page else total // per_page + 1
        query = query.limit(per_page).offset((page - 1) * per_page)  # type: ignore

        db_execute = await db.execute(query)
        return db_execute.scalars().all(), total, pages
