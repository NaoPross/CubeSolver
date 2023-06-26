
class Vec3:
	def __init__(self, *coords):
		# Basis vectors e1, e2, e3
		self.coords = coords
		self.dim = len(self.coords)

	def inner(self, other):
		''' left inner product self . other '''
		return sum(uu * vv for uu, vv in zip(self, other))

	def rinner(self, other):
		''' right inner product other . self '''
		# inner product is symmetric
		return self.inner(other)

	def outer(self, other):
		''' left outer product self ^ other '''
		u1, u2, u3 = self
		v1, v2, v3 = other
		return BiVec3(u1 * v2 - u2 * v1,
						u1 * v3 - v3 * u1,
						u2 * v3 - u3 * v2)

	def __repr__(self):
		return f"<Vec{self.dim} {self.coords}>"
	
	def __iter__(self):
		return iter(self.coords)

	def __add__(self, other):
		assert self.dim == other.dim
		v = tuple(e + o for e, o in zip(self, other))
		return Vec3(*v)

	def __radd__(self, other):
		return self.__add__(other)

	def __mul__(self, scalar):
		v = tuple(scalar * e for e in self.coords)
		return Vec3(*v)

	def __rmul__(self, scalar):
		return self.__mul__(scalar)


class BiVec3:
	def __init__(self, *coords):
		# Basis vectors e12, e13, e23
		self.coords = coords


class TriVec3:
	def __init__(self, c):
		# Basis vector e123
		self.coords = (c,)


class MultiVec3:
	def __init__(self, scalar, vec, bivec, trivec):
		self.scalar = scalar
		self.vec = vec
		self.bivec = bivec
		self.trivec = trivec

def vec_geom(u, v):
	return MultiVec3(vec_inner(u, v), Vec(0, 0, 0), vec_outer(u, v))
