"""Написать программу, которая по заданной формуле строит дерево и
производит вычисления с помощью построенного дерева. Формула задана в
традиционной инфиксной записи, в ней могут быть скобки, максимальная
степень вложенности которых ограничивается числом 10. Аргументами могут
быть целые числа и переменные, задаваемые однобуквенными именами.
Допустимые операции: +, -, *, /. Унарный минус допустим. С помощью
построенного дерева формулы упростить формулу, заменяя в ней все
поддеревья, соответствующие формулам (f1*f3±f2*f3) и (f1*f2±f1*f3) на
поддеревья, соответствующие формулам ((f1±f2)*f3) и (f1*(f2±f3)).
"""

from typing import Dict


class ParseError(Exception):
    """Ошибка разбора выражения."""
    pass


class Node:
    """Базовый класс для всех узлов выражения."""

    def evaluate(self, variables: Dict[str, int]) -> int:
        """Вычисляет значение выражения.

        Args:
            variables (Dict[str, int]): Значения переменных.

        Returns:
            int: Результат выражения.
        """
        raise NotImplementedError()

    def simplify(self) -> 'Node':
        """Упрощает выражение.

        Returns:
            Node: Упрощённое выражение.
        """
        return self

    def to_infix(self) -> str:
        """Преобразует выражение в инфиксную строку.

        Returns:
            str: Инфиксная форма выражения.
        """
        raise NotImplementedError()


class ValueNode(Node):
    """Узел, представляющий число или переменную."""

    def __init__(self, value):
        self.value = value

    def evaluate(self, variables: Dict[str, int]) -> int:
        if isinstance(self.value, int):
            return self.value
        elif self.value in variables:
            return variables[self.value]
        else:
            raise ValueError(f"Переменная '{self.value}' не определена.")

    def to_infix(self) -> str:
        return str(self.value)

    def __eq__(self, other):
        return isinstance(other, ValueNode) and self.value == other.value


class UnaryMinusNode(Node):
    """Узел для унарного минуса."""

    def __init__(self, child: Node):
        self.child = child

    def evaluate(self, variables: Dict[str, int]) -> int:
        return -self.child.evaluate(variables)

    def simplify(self) -> Node:
        self.child = self.child.simplify()
        if isinstance(self.child, ValueNode) and isinstance(self.child.value, int):
            return ValueNode(-self.child.value)
        return self

    def to_infix(self) -> str:
        return f"-({self.child.to_infix()})"


class BinaryOpNode(Node):
    """Узел для бинарных операций (+, -, *, /)."""

    OPERATORS_PRIORITY = {'+': 1, '-': 1, '*': 2, '/': 2}

    def __init__(self, op: str, left: Node, right: Node):
        self.op = op
        self.left = left
        self.right = right

    def evaluate(self, variables: Dict[str, int]) -> int:
        left_val = self.left.evaluate(variables)
        right_val = self.right.evaluate(variables)
        if self.op == '+':
            return left_val + right_val
        elif self.op == '-':
            return left_val - right_val
        elif self.op == '*':
            return left_val * right_val
        elif self.op == '/':
            if right_val == 0:
                raise ZeroDivisionError("Деление на ноль")
            return left_val // right_val
        else:
            raise ValueError(f"Неизвестный оператор: {self.op}")

    def simplify(self) -> Node:
        self.left = self.left.simplify()
        self.right = self.right.simplify()

        if (self.op in ('+', '-') and isinstance(self.left, BinaryOpNode)
                and isinstance(self.right, BinaryOpNode)):
            if self.left.op == '*' and self.right.op == '*':
                l1, l2 = self.left.left, self.left.right
                r1, r2 = self.right.left, self.right.right
                if l2 == r2:
                    return BinaryOpNode(
                        '*',
                        BinaryOpNode(self.op, l1, r1).simplify(),
                        l2
                    ).simplify()
                if l1 == r1:
                    return BinaryOpNode(
                        '*',
                        l1,
                        BinaryOpNode(self.op, l2, r2).simplify()
                    ).simplify()

        if isinstance(self.left, ValueNode) and isinstance(self.right, ValueNode):
            if isinstance(self.left.value, int) and isinstance(self.right.value, int):
                return ValueNode(self.evaluate({}))

        return self

    def to_infix(self) -> str:
        return f"({self.left.to_infix()} {self.op} {self.right.to_infix()})"

    def __eq__(self, other):
        return (
            isinstance(other, BinaryOpNode)
            and self.op == other.op
            and self.left == other.left
            and self.right == other.right
        )


class Parser:
    """Парсер инфиксных арифметических выражений."""

    OPERATORS_PRIORITY = {'+': 1, '-': 1, '*': 2, '/': 2}

    def __init__(self, expr: str):
        self.expr = expr.replace(' ', '')
        self.pos = 0

    def parse(self) -> Node:
        """Парсит выражение.

        Returns:
            Node: Корень дерева выражения.

        Raises:
            ParseError: При синтаксической ошибке.
        """
        result = self._parse_expression()
        if self.pos != len(self.expr):
            raise ParseError("Неожиданные символы в конце выражения.")
        return result

    def _parse_expression(self, min_priority=0) -> Node:
        node = self._parse_unary()
        while (self._current() in self.OPERATORS_PRIORITY
               and self._priority(self._current()) >= min_priority):
            op = self._consume()
            right = self._parse_expression(self._priority(op) + 1)
            node = BinaryOpNode(op, node, right)
        return node

    def _parse_unary(self) -> Node:
        if self._current() == '-':
            self._consume()
            return UnaryMinusNode(self._parse_unary())
        return self._parse_primary()

    def _parse_primary(self) -> Node:
        ch = self._current()
        if ch == '(':
            self._consume()
            node = self._parse_expression()
            if self._current() != ')':
                raise ParseError("Ожидалась закрывающая скобка.")
            self._consume()
            return node
        elif ch.isdigit():
            return self._parse_number()
        elif ch.isalpha():
            return ValueNode(self._consume())
        else:
            raise ParseError(f"Неожиданный символ: '{ch}'")

    def _parse_number(self) -> ValueNode:
        start = self.pos
        while self._current().isdigit():
            self.pos += 1
        return ValueNode(int(self.expr[start:self.pos]))

    def _current(self) -> str:
        return self.expr[self.pos] if self.pos < len(self.expr) else ''

    def _consume(self) -> str:
        ch = self._current()
        self.pos += 1
        return ch

    def _priority(self, op: str) -> int:
        return self.OPERATORS_PRIORITY.get(op, 0)


if __name__ == "__main__":
    try:
        expr = input("Введите инфиксную формулу (например, a*c + b*c): ")
        parser = Parser(expr)
        tree = parser.parse()

        print("Исходное выражение:", tree.to_infix())

        simplified = tree.simplify()
        print("Упрощённое выражение:", simplified.to_infix())

        answer = input("Вычислить выражение? (y/n): ").strip().lower()
        if answer == 'y':
            variables = {}
            for ch in set(filter(str.isalpha, expr)):
                try:
                    value = int(input(f"Введите значение переменной '{ch}': "))
                    variables[ch] = value
                except ValueError:
                    print("Ошибка: требуется целое число.")
                    raise
            result = simplified.evaluate(variables)
            print("Результат:", result)
    except ParseError as pe:
        print("Ошибка парсинга:", pe)
    except ZeroDivisionError:
        print("Ошибка: деление на ноль.")
    except ValueError as ve:
        print("Ошибка:", ve)
    except Exception as e:
        print("Непредвиденная ошибка:", e)
