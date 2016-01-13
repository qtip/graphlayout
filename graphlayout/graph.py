import math

from collections import defaultdict
from collections import namedtuple
from collections import OrderedDict


Link = namedtuple('Link', ('target_obj', 'src_ratio', 'target_ratio', 'offset'))


class DimensionLinks:

    def __init__(self):
        self.negative_link = None
        self.center_link = None
        self.positive_link = None

    def __iter__(self):
        if self.negative_link:
            yield self.negative_link
        if self.center_link:
            yield self.center_link
        if self.positive_link:
            yield self.positive_link

    def link_to(self, target_object, src_ratio, target_ratio, offset):
        offset *= math.copysign(1, 0.5 - src_ratio)
        link = Link(target_object, src_ratio, target_ratio, offset)
        if src_ratio < 0.5:
            self.negative_link = link
        elif src_ratio > 0.5:
            self.positive_link = link
        else:
            self.center_link = link

    def unlink(self, src_ratio):
        if src_ratio < 0.5:
            self.negative_link = None
        elif src_ratio > 0.5:
            self.positive_link = None
        else:
            self.center_link = None

    def __eq__(self, other):
        return (
            (self.negative_link, self.center_link, self.positive_link) ==
            (other.negative_link, other.center_link, other.positive_link)
        )


class LinkerMethod:

    def __init__(self, node, dimension_links, src_ratio, target_ratio):
        self.node = node
        self.dimension_links = dimension_links
        self.src_ratio = src_ratio
        self.target_ratio = target_ratio

    def __call__(self, other_obj, offset=0):
        self.dimension_links.link_to(other_obj, self.src_ratio, self.target_ratio, offset)
        return self.node

    def __eq__(self, other):
        return (
            (self.node, self.dimension_links,
             self.src_ratio, self.target_ratio) ==
            (other.node, other.dimension_links,
             other.src_ratio, other.target_ratio)
        )


class Node:
    def __init__(self, graph, obj):
        self.graph = graph
        self.obj = obj
        self.x_links = DimensionLinks()
        self.y_links = DimensionLinks()
        self.z_links = DimensionLinks()
        self._width = 0
        self._height = 0

    def top_unlink(self):
        self.y_links.unlink(0)
        return self

    def middle_unlink(self):
        self.y_links.unlink(0)
        return self

    def bottom_unlink(self):
        self.y_links.unlink(1)
        return self

    def left_unlink(self):
        self.x_links.unlink(0)
        return self

    def center_unlink(self):
        self.x_links.unlink(0.5)
        return self

    def right_unlink(self):
        self.x_links.unlink(1)
        return self

    def inside(self, other_obj, offset=0):
        return self \
            .left_to_left(other_obj, offset) \
            .top_to_top(other_obj, offset) \
            .right_to_right(other_obj, offset) \
            .bottom_to_bottom(other_obj, offset)

    def height(self, px):
        self._height = px
        return self

    def width(self, px):
        self._width = px
        return self

    def _edges(self):
        seen = set()
        if self.x_links.negative_link:
            edge = self.obj, self.x_links.negative_link.target_obj
            if edge not in seen:
                yield edge
            seen.add(edge)
        if self.x_links.center_link:
            edge = self.obj, self.x_links.center_link.target_obj
            if edge not in seen:
                yield edge
            seen.add(edge)
        if self.x_links.positive_link:
            edge = self.obj, self.x_links.positive_link.target_obj
            if edge not in seen:
                yield edge
            seen.add(edge)
        if self.y_links.negative_link:
            edge = self.obj, self.y_links.negative_link.target_obj
            if edge not in seen:
                yield edge
            seen.add(edge)
        if self.y_links.center_link:
            edge = self.obj, self.y_links.center_link.target_obj
            if edge not in seen:
                yield edge
            seen.add(edge)
        if self.y_links.positive_link:
            edge = self.obj, self.y_links.positive_link.target_obj
            if edge not in seen:
                yield edge
            seen.add(edge)

    def __repr__(self):
        out = []
        out.append("{cls}({self.obj!r})".format(cls=self.__class__.__name__, self=self))
        return '.'.join(out)


def _link_method_generator(from_name, from_value, to_name, to_value):
    """
    Generates a method named [from_name]_to_[to_name] to be set on the
    Node class.

    The methods created are function factories for creating LinkerMethod
    instances with the correct source and target ratios.

    Returns:
        the generated method
    """
    def method(self):
        return LinkerMethod(self, self.x_links, from_value, to_value)
    method.__name__ = '{}_to_{}'.format(from_name, to_name)
    return method


seeds = (
    {'left': 0, 'center': 0.5, 'right': 1},
    {'top': 0, 'middle': 0.5, 'bottom': 1}
)

method = None
method_attrs = None
for method_attrs in seeds:
    for name1, value1 in method_attrs.items():
        for name2, value2 in method_attrs.items():
            if name1 != name2:
                method = _link_method_generator(name1, value1, name2, value2)
                setattr(Node, method.__name__, method)
del method
del method_attrs
del seeds


class Box:

    def __init__(self, l=0, t=0, r=0, b=0):
        self.l = l
        self.t = t
        self.r = r
        self.b = b

    def __repr__(self):
        return "Box(l={l}, t={t}, r={r}, b={b})".format(l=self.l, t=self.t, r=self.r, b=self.b)

    @property
    def w(self):
        return self.r - self.l

    @property
    def h(self):
        return self.b - self.t

    def union(self, other):
        if other.l < self.l:
            self.l = other.l
        if self.r < other.r:
            self.r = other.r
        if other.t < self.t:
            self.t = other.t
        if self.b < other.b:
            self.b = other.b


class Origin:

    def __repr__(self):
        return self.__class__.__name__ + "()"


class Graph:

    def __init__(self):
        self._origin = Origin()
        self._previous = [self._origin, self._origin]
        self.nodes = OrderedDict()
        self._dirty = True
        self._order = []
        self._boxes = defaultdict(Box)
        self._bounding_box = Box()

    @property
    def ORIGIN(self):
        return self._origin

    @property
    def previous(self):
        return self._previous[1]

    def node(self, obj):
        self.nodes[obj] = Node(self, obj)
        self._previous.pop()
        self._previous.insert(0, obj)
        return self.nodes[obj]

    def remove(self, obj):
        del self.nodes[obj]

    def _edges(self):
        for node in self.nodes.values():
            yield from node._edges()

    def _update_order(self):
        self._order.clear()
        incoming = OrderedDict()
        outgoing = OrderedDict()
        for src, dst in self._edges():
            if src not in outgoing:
                outgoing[src] = OrderedDict()
            outgoing[src][dst] = True
            if dst not in incoming:
                incoming[dst] = OrderedDict()
            incoming[dst][src] = True

        leaves = [node for node in outgoing.keys() if node not in incoming]
        while leaves:
            leaf = leaves.pop()
            self._order.insert(0, leaf)
            if leaf in outgoing:
                for dst in outgoing[leaf].copy():
                    del incoming[dst][leaf]
                    if not incoming[dst]:
                        leaves.append(dst)
                        del incoming[dst]
                    del outgoing[leaf][dst]
        if incoming:
            raise Exception("Cycles detected")

    def _update_boxes(self):
        self._boxes.clear()
        for obj in self._order:
            if obj is self.ORIGIN:
                self._boxes[self.ORIGIN] = Box(0, 0, 0, 0)
                continue
            node = self.nodes[obj]
            box = Box()

            # find final box width
            if node._width:
                width = node._width
            else:
                a, b = (self._boxes[target_obj].w * target_ratio + offset for target_obj, _, target_ratio, offset in node.x_links)
                h, j = (src_ratio for _, src_ratio, _, _ in node.x_links)
                width = (b - a) / (j - h)
            # position the box based on the width
            x_iter = iter(node.x_links)
            target_obj, src_ratio, target_ratio, offset = next(x_iter)
            target_box = self._boxes[target_obj]
            target_px = target_box.l + target_box.w * target_ratio + offset
            box.l = target_px - width * src_ratio
            box.r = target_px + width * (1 - src_ratio)

            # find final box height
            if node._height:
                height = node._height
            else:
                a, b = (self._boxes[target_obj].h * target_ratio + offset for target_obj, _, target_ratio, offset in node.y_links)
                h, j = (src_ratio for _, src_ratio, _, _ in node.y_links)
                height = (b - a) / (j - h)
            # position the box based on the height
            y_iter = iter(node.y_links)
            target_obj, src_ratio, target_ratio, offset = next(y_iter)
            target_box = self._boxes[target_obj]
            target_px = target_box.t + target_box.h * target_ratio + offset
            box.t = target_px - height * src_ratio
            box.b = target_px + height * (1 - src_ratio)

            self._bounding_box.union(box)
            self._boxes[obj] = box

    def layout(self, positioner):
        if self._dirty:
            self._update_order()
            self._update_boxes()
            self._dirty = False
        for obj in self._order:
            if obj == self.ORIGIN:
                continue
            node = self.nodes[obj]
            box = self._boxes[obj]
            x = box.l - self._bounding_box.l
            y = box.t - self._bounding_box.t
            positioner(obj, x, y, box.w, box.h)
