# /// script
# requires-python = ">=3.12"
# dependencies = ["marimo"]
# ///

import marimo

__generated_with = "0.26.0"
app = marimo.App(width="medium", app_title="Example")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md("""
    # Example

    This page was exported with `marimo export html-wasm`. Python runs **in your browser**,
    so the controls below are live.
    """)
    return


@app.cell
def _(mo):
    n = mo.ui.slider(1, 20, value=8, label="Points")
    amp = mo.ui.slider(1, 10, value=5, label="Amplitude")
    mo.hstack([n, amp], justify="start")
    return amp, n


@app.cell
def _(amp, mo, n):
    import math

    _rows = [{"x": i, "y": round(amp.value * math.sin(i / 2), 3)} for i in range(n.value)]
    mo.ui.table(_rows, selection=None)
    return


if __name__ == "__main__":
    app.run()
