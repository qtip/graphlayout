from graphlayout.graph import Node, Box, Graph, LinkerMethod, DimensionLinks

from tests.testcase import BaseTestCase


class TestNodeMethodGeneration(BaseTestCase):

    def setUp(self):
        self.node = Node(Graph(), Box())

    def test_left_to_right(self):
        method = self.node.left_to_right()
        self.assertEqual(method, LinkerMethod(
                self.node, DimensionLinks(), 0, 1))

    def test_right_to_left(self):
        method = self.node.right_to_left()
        self.assertEqual(method, LinkerMethod(
                self.node, DimensionLinks(), 1, 0))
