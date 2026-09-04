import ast
import operator
import math
import re

# Supported safe operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "abs": abs,
    "round": round,
    "log": math.log,
    "pi": math.pi,
    "e": math.e
}

def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported operator: {op_type.__name__}")
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in SAFE_FUNCTIONS:
            func = SAFE_FUNCTIONS[node.func.id]
            args = [_eval_node(arg) for arg in node.args]
            return func(*args)
        raise ValueError("Unsupported function call")
    elif isinstance(node, ast.Name) and node.id in SAFE_FUNCTIONS:
        return SAFE_FUNCTIONS[node.id]
    raise ValueError(f"Unsupported AST node: {type(node).__name__}")

def calculate(expression: str) -> str:
    """
    Safely evaluates a math expression without using unrestricted eval().
    Supports standard math, percentages ('25% of 800', '25 percent of 800'),
    and spoken phrases ('100 divided by 4', '5 times 12').
    """
    expression = expression.strip()
    
    # Handle percentage syntax: e.g. "25% of 800" or "25 percent of 800"
    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:%|percent)\s*(?:of)?\s*(\d+(?:\.\d+)?)', expression, re.IGNORECASE)
    if pct_match:
        pct = float(pct_match.group(1))
        val = float(pct_match.group(2))
        res = (pct / 100.0) * val
        if res.is_integer():
            res = int(res)
        unit = "percent" if "percent" in expression.lower() else "%"
        return f"{pct:g} {unit} of {val:g} is {res}."
    
    # Handle simple unit conversions
    km_match = re.search(r'(\d+(?:\.\d+)?)\s*km\s*(?:to\s*m(?:eters)?)?', expression, re.IGNORECASE)
    if km_match:
        km = float(km_match.group(1))
        return f"{km} km = {km * 1000:g} meters"

    try:
        # Convert natural language operators to math symbols
        clean_expr = expression.lower()
        clean_expr = re.sub(r'^(?:what is|how much is|calculate)\s*', '', clean_expr).strip()
        clean_expr = clean_expr.replace("divided by", "/").replace("over", "/")
        clean_expr = clean_expr.replace("multiplied by", "*").replace("times", "*")
        clean_expr = clean_expr.replace("plus", "+").replace("minus", "-")
        clean_expr = clean_expr.replace("^", "**").replace("x", "*")
        clean_expr = re.sub(r'[^0-9a-z\+\-\*\/\(\)\.\s]', '', clean_expr)

        tree = ast.parse(clean_expr, mode='eval')
        result = _eval_node(tree.body)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"
