
from flask import Flask, render_template, request, jsonify
import ast
import operator

app = Flask(__name__)

# Allowed mathematical operations
operators = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow
}


def calculate(node):
    if isinstance(node, ast.Expression):
        return calculate(node.body)

    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in operators:
        left = calculate(node.left)
        right = calculate(node.right)

        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("Power too large")

        return operators[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and isinstance(
        node.op, (ast.UAdd, ast.USub)
    ):
        value = calculate(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value

    raise ValueError("Invalid expression")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/calculate", methods=["POST"])
def calculate_result():
    try:
        data = request.get_json()
        expression = data.get("expression", "")

        if not isinstance(expression, str) or len(expression) > 100:
            raise ValueError("Invalid expression")

        tree = ast.parse(expression, mode="eval")
        result = calculate(tree)

        if not isinstance(result, (int, float)):
            raise ValueError("Invalid result")

        if abs(result) > 1e15:
            raise ValueError("Result too large")

        return jsonify({"result": result})

    except ZeroDivisionError:
        return jsonify({"error": "Cannot divide by zero"}), 400

    except (ValueError, SyntaxError, TypeError, OverflowError):
        return jsonify({"error": "Invalid calculation"}), 400


if __name__ == "__main__":
    app.run(debug=True)
