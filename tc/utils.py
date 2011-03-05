
def get_ancestors(node):
    """
    Given a template node, returns an ordered list of all the nodes which are
    above it in the template tree.
    """
    node_path = []
    parent = node.parent
    while parent:
        node_path.append(parent)
        parent = parent.parent
    node_path.reverse()
    return node_path
