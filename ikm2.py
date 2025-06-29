"""
Написать программу, которая по заданной формуле строит дерево и
производит вычисления с помощью построенного дерева. Формула задана в
традиционной инфиксной записи, в ней могут быть скобки, максимальная
степень вложенности которых ограничивается числом 10. Аргументами могут
быть целые числа и переменные, задаваемые однобуквенными именами.
Допустимые операции: +, -, *, /. Унарный минус допустим. С помощью
построенного дерева формулы упростить формулу, заменяя в ней все
поддеревья, соответствующие формулам (f1*f3±f2*f3) и (f1*f2±f1*f3) на
поддеревья, соответствующие формулам ((f1±f2)*f3) и (f1*(f2±f3)).
"""


class Node:
    def evaluate(self, variables):
        raise NotImplementedError()

    def simplify(self):
        return self

    def to_infix(self):
        raise NotImplementedError()


class ValueNode(Node):
    def __init__(self, value):
        self.value = value

    def evaluate(self, variables):
        if isinstance(self.value, int):
            return self.value
        if self.value in variables:
            return variables[self.value]
        raise ValueError("Переменная '{}' не определена.".format(self.value))

    def to_infix(self):
        return str(self.value)

    def __eq__(self, other):
        return isinstance(other, ValueNode) and self.value == other.value


class UnaryMinusNode(Node):
    def __init__(self, child):
        self.child = child

    def evaluate(self, variables):
        return -self.child.evaluate(variables)

    def simplify(self):
        self.child = self.child.simplify()
        if isinstance(self.child, ValueNode) and isinstance(self.child.value, int):
            return ValueNode(-self.child.value)
        return self

    def to_infix(self):
        return "-({})".format(self.child.to_infix())


class BinaryOpNode(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def evaluate(self, variables):
        left_val = self.left.evaluate(variables)
        right_val = self.right.evaluate(variables)

        if self.op == '+':
            return left_val + right_val
        if self.op == '-':
            return left_val - right_val
        if self.op == '*':
            return left_val * right_val
        if self.op == '/':
            if right_val == 0:
                raise ZeroDivisionError("Деление на ноль")
            return left_val // right_val
        raise ValueError("Неизвестный оператор: {}".format(self.op))

    def simplify(self):
        self.left = self.left.simplify()
        self.right = self.right.simplify()

        if (self.op in ('+', '-') and isinstance(self.left, BinaryOpNode)
                and isinstance(self.right, BinaryOpNode)):
            if self.left.op == '*' and self.right.op == '*':
                l1, l2 = self.left.left, self.left.right
                r1, r2 = self.right.left, self.right.right
                if l2 == r2:
                    return BinaryOpNode('*', BinaryOpNode(self.op, l1, r1).simplify(), l2).simplify()
                if l1 == r1:
                    return BinaryOpNode('*', l1, BinaryOpNode(self.op, l2, r2).simplify()).simplify()

        if isinstance(self.left, ValueNode) and isinstance(self.right, ValueNode):
            if isinstance(self.left.value, int) and isinstance(self.right.value, int):
                return ValueNode(self.evaluate({}))

        return self

    def to_infix(self):
        return "({} {} {})".format(self.left.to_infix(), self.op, self.right.to_infix())

    def __eq__(self, other):
        return (
            isinstance(other, BinaryOpNode)
            and self.op == other.op
            and self.left == other.left
            and self.right == other.right
        )


def parse_expression(expr):
    expr = expr.replace(' ', '')
    pos = 0

    def current():
        if pos < len(expr):
            return expr[pos]
        return ''

    def consume():
        nonlocal pos
        ch = current()
        pos += 1
        return ch

    def priority(op):
        priorities = {'+': 1, '-': 1, '*': 2, '/': 2}
        return priorities.get(op, 0)

    def parse_number():
        nonlocal pos
        start = pos
        while current().isdigit():
            pos += 1
        return ValueNode(int(expr[start:pos]))

    def parse_primary():
        ch = current()
        if ch == '(':
            consume()
            node = parse_expression_inner()
            if current() != ')':
                raise SyntaxError("Ожидалась закрывающая скобка.")
            consume()
            return node
        if ch.isdigit():
            return parse_number()
        if ch.isalpha():
            return ValueNode(consume())
        raise SyntaxError("Неожиданный символ: '{}'".format(ch))

    def parse_unary():
        if current() == '-':
            consume()
            return UnaryMinusNode(parse_unary())
        return parse_primary()

    def parse_expression_inner(min_priority=0):
        node = parse_unary()
        while current() != '' and current() in '+-*/' and priority(current()) >= min_priority:
            op = consume()
            right = parse_expression_inner(priority(op) + 1)
            node = BinaryOpNode(op, node, right)
        return node

    tree = parse_expression_inner()
    if pos != len(expr):
        raise SyntaxError("Неожиданные символы в конце выражения.")
    return tree


def main():
    try:
        expr = input("Введите инфиксную формулу (например, a*c + b*c): ").strip()
        tree = parse_expression(expr)

        print("Исходное выражение:", tree.to_infix())

        simplified = tree.simplify()
        print("Упрощённое выражение:", simplified.to_infix())

        if input("Вычислить выражение? (y/n): ").strip().lower() == 'y':
            variables = {}
            for ch in sorted(set(filter(str.isalpha, expr))):
                while True:
                    try:
                        value = int(input("Введите значение переменной '{}': ".format(ch)))
                        variables[ch] = value
                        break
                    except ValueError:
                        print("Ошибка: требуется целое число.")
            result = simplified.evaluate(variables)
            print("Результат:", result)

    except (ValueError, SyntaxError, ZeroDivisionError) as e:
        print("Ошибка:", e)


if __name__ == '__main__':
    main()

