from enum import Enum, EnumMeta

__all__ = ("GradeLevel",)


class ContainsGradeMeta(EnumMeta):
    def __contains__(cls, val) -> bool:
        """Returns True if val matches a key
        or a value
        """
        if isinstance(val, cls):
            return super().__contains__(val)
        elif isinstance(val, str):
            return val in {grade.name for grade in cls}  # noqa: E1133 pylint: disable=not-an-iterable
        elif isinstance(val, int):
            return val in {grade.value for grade in cls}  # noqa: E1133 pylint: disable=not-an-iterable

        return False


class GradeLevel(Enum, metaclass=ContainsGradeMeta):
    freshman = 9
    sophmore = 10
    junior = 11
    senior = 12
    staff = 13
