import pytest
from shared.dag import TaskGraph, TaskNode

def test_execution_order_linear():
    node1 = TaskNode(id="1", skill_name="s1", action="a1", input_template={}, dependencies=[])
    node2 = TaskNode(id="2", skill_name="s1", action="a2", input_template={}, dependencies=["1"])
    graph = TaskGraph(graph_id="g1", nodes={"1": node1, "2": node2})
    
    order = graph.get_execution_order()
    assert order == [["1"], ["2"]]

def test_execution_order_branching():
    node1 = TaskNode(id="1", skill_name="s1", action="a1", input_template={}, dependencies=[])
    node2 = TaskNode(id="2", skill_name="s1", action="a2", input_template={}, dependencies=["1"])
    node3 = TaskNode(id="3", skill_name="s1", action="a3", input_template={}, dependencies=["1"])
    node4 = TaskNode(id="4", skill_name="s1", action="a4", input_template={}, dependencies=["2", "3"])
    
    graph = TaskGraph(graph_id="g1", nodes={"1": node1, "2": node2, "3": node3, "4": node4})
    
    order = graph.get_execution_order()
    assert order[0] == ["1"]
    assert set(order[1]) == {"2", "3"}
    assert order[2] == ["4"]

def test_execution_order_circular():
    node1 = TaskNode(id="1", skill_name="s1", action="a1", input_template={}, dependencies=["2"])
    node2 = TaskNode(id="2", skill_name="s1", action="a2", input_template={}, dependencies=["1"])
    graph = TaskGraph(graph_id="g1", nodes={"1": node1, "2": node2})
    
    with pytest.raises(ValueError, match="circular dependencies"):
        graph.get_execution_order()

def test_execution_order_missing_dep():
    node1 = TaskNode(id="1", skill_name="s1", action="a1", input_template={}, dependencies=["non-existent"])
    
    with pytest.raises(ValueError, match="missing dependency"):
        TaskGraph(graph_id="g1", nodes={"1": node1})
