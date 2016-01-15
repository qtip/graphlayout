from graphlayout.graph import Node, Box, Graph, LinkerMethod, DimensionLinks

from tests.testcase import BaseTestCase


class TestLayout(BaseTestCase):

    def setUp(self):
        pass

    def test_x(self):
        graph = Graph()
        graph.node('.').middle_to_middle(graph.ORIGIN).center_to_center(graph.ORIGIN).width(40).height(15)
        graph.node('\\/').inside('.').top_unlink().height(5)
        graph.node('|').inside('.').bottom_unlink().height(3)
        graph.node('search bar   ').middle_to_middle('|').left_to_left('|', 5).right_to_right('|', 5).height(1)
        out = [[' ' for i in range(40)] for j in range(15)]

        def positioner(c, x, y, w, h):
            for c_y in range(int(y), int(y + h)):
                for c_x in range(int(x), int(x + w)):
                    out[c_y][c_x] = c[int(c_x - x + (c_y - y)) % len(c)]
        graph.layout(positioner)
        for line in out:
            print(''.join(line))
