from dataclasses import dataclass
from typing import Any, Iterable, Tuple

from typing_extensions import Protocol

# ## Task 1.1
# Central Difference calculation


def central_difference(f: Any, *vals: Any, arg: int = 0, epsilon: float = 1e-6) -> Any:
    r"""
    Computes an approximation to the derivative of `f` with respect to one arg.

    See :doc:`derivative` or https://en.wikipedia.org/wiki/Finite_difference for more details.

    Args:
        f : arbitrary function from n-scalar args to one value
        *vals : n-float values $x_0 \ldots x_{n-1}$
        arg : the number $i$ of the arg to compute the derivative
        epsilon : a small constant

    Returns:
        An approximation of $f'_i(x_0, \ldots, x_{n-1})$
    """
    _vals = list(vals)
    new_vals_left = _vals.copy()
    new_vals_right = _vals.copy()
    new_vals_left[arg] -= epsilon
    new_vals_right[arg] += epsilon
    return (f(*new_vals_right) - f(*new_vals_left)) / (2 * epsilon)


variable_count = 1


class Variable(Protocol):
    def accumulate_derivative(self, x: Any) -> None:
        pass

    @property
    def unique_id(self) -> int:
        pass

    def is_leaf(self) -> bool:
        pass

    def is_constant(self) -> bool:
        pass

    @property
    def parents(self) -> Iterable["Variable"]:
        pass

    def chain_rule(self, d_output: Any) -> Iterable[Tuple["Variable", Any]]:
        pass


def topological_sort(variable: Variable) -> Iterable[Variable]:
    """
    Computes the topological order of the computation graph.

    Args:
        variable: The right-most variable

    Returns:
        Non-constant Variables in topological order starting from the right.
    """
    ret = []
    visited = []
    temp_mark = []
    def visit(cur_var: Variable):
        if cur_var.is_constant():
            return
        if cur_var.unique_id in visited:
            return
        if cur_var.unique_id in temp_mark:
            raise RuntimeError('Not an DAG!')
        temp_mark.append(cur_var.unique_id)
        if not cur_var.is_leaf():
            for parent in cur_var.parents:
                visit(parent)
        
        temp_mark.remove(cur_var.unique_id)
        visited.append(cur_var.unique_id)
        ret.insert(0, cur_var)

    visit(variable)
    return ret


def backpropagate(variable: Variable, deriv: Any) -> None:
    """
    Runs backpropagation on the computation graph in order to
    compute derivatives for the leave nodes.

    Args:
        variable: The right-most variable
        deriv  : Its derivative that we want to propagate backward to the leaves.

    No return. Should write to its results to the derivative values of each leaf through `accumulate_derivative`.
    """
    topo_result: Iterable[Variable] = topological_sort(variable)
    derivs = {variable.unique_id: deriv}
    for cur_var in topo_result:
        d_out = derivs[cur_var.unique_id]
        if cur_var.is_leaf():
            cur_var.accumulate_derivative(d_out)
        else:
            for inp, d in cur_var.chain_rule(d_out):
                if inp.unique_id not in derivs.keys():
                    derivs[inp.unique_id] = 0.0
                derivs[inp.unique_id] += d


@dataclass
class Context:
    """
    Context class is used by `Function` to store information during the forward pass.
    """

    no_grad: bool = False
    saved_values: Tuple[Any, ...] = ()

    def save_for_backward(self, *values: Any) -> None:
        "Store the given `values` if they need to be used during backpropagation."
        if self.no_grad:
            return
        self.saved_values = values

    @property
    def saved_tensors(self) -> Tuple[Any, ...]:
        return self.saved_values
