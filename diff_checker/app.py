from flask import Flask, render_template, request, jsonify
import difflib

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("./index.html")


@app.route("/diff", methods=["POST"])
def diff():
    data = request.get_json()
    original = data.get("original", "")
    modified = data.get("modified", "")
    mode = data.get("mode", "unified")
    context = int(data.get("context", 3))

    lines_a = original.splitlines(keepends=True)
    lines_b = modified.splitlines(keepends=True)

    if mode == "unified":
        result = unified_diff(lines_a, lines_b, context)
    else:
        result = side_by_side_diff(lines_a, lines_b)

    adds = sum(1 for h in result["hunks"] for l in h["lines"] if l["type"] == "add")
    dels = sum(1 for h in result["hunks"] for l in h["lines"] if l["type"] == "del")
    result["stats"] = {"adds": adds, "dels": dels, "identical": adds == 0 and dels == 0}
    return jsonify(result)


def unified_diff(lines_a, lines_b, context):
    raw = list(difflib.unified_diff(lines_a, lines_b, n=context))
    hunks = []
    current = None

    for line in raw:
        stripped = line.rstrip("\n")
        if stripped.startswith("---") or stripped.startswith("+++"):
            continue
        if stripped.startswith("@@"):
            if current:
                hunks.append(current)
            current = {"header": stripped, "lines": []}
        elif current is not None:
            if stripped.startswith("+"):
                current["lines"].append({"type": "add", "text": stripped[1:]})
            elif stripped.startswith("-"):
                current["lines"].append({"type": "del", "text": stripped[1:]})
            else:
                current["lines"].append({"type": "ctx", "text": stripped[1:]})

    if current:
        hunks.append(current)

    return {"mode": "unified", "hunks": hunks}


def side_by_side_diff(lines_a, lines_b):
    matcher = difflib.SequenceMatcher(None, lines_a, lines_b, autojunk=False)
    rows = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        left = [l.rstrip("\n") for l in lines_a[i1:i2]]
        right = [l.rstrip("\n") for l in lines_b[j1:j2]]
        pairs = list(zip(left, right))
        extra_left = left[len(pairs) :]
        extra_right = right[len(pairs) :]

        for l, r in pairs:
            t = "ctx" if tag == "equal" else "chg"
            rows.append(
                {
                    "left": l,
                    "right": r,
                    "type": t,
                    "left_type": "ctx" if tag == "equal" else "del",
                    "right_type": "ctx" if tag == "equal" else "add",
                }
            )
        for l in extra_left:
            rows.append(
                {
                    "left": l,
                    "right": "",
                    "type": "chg",
                    "left_type": "del",
                    "right_type": "empty",
                }
            )
        for r in extra_right:
            rows.append(
                {
                    "left": "",
                    "right": r,
                    "type": "chg",
                    "left_type": "empty",
                    "right_type": "add",
                }
            )

    return {"mode": "side", "hunks": [{"header": "", "lines": rows}]}


if __name__ == "__main__":
    app.run(debug=True)
