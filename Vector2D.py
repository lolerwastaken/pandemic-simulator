from __future__ import annotations

class Vector2D:
    x:float
    y:float

    def zero() -> Vector2D:
        return Vector2D(0,0)

    def lerp(v1:Vector2D, v2:Vector2D, t:float) -> Vector2D:
        return (v2 - v1)*t + v1
    
    def add(v1:Vector2D, v2:Vector2D) -> Vector2D:
        return Vector2D(v1.x + v2.x, v1.y + v2.y)
    
    def sub(v1:Vector2D, v2:Vector2D) -> Vector2D:
        return Vector2D.add(v1, Vector2D.scale(v2, -1))

    def scale(v:Vector2D, other:int | float | Vector2D) -> Vector2D:
        if isinstance(other, (int, float)):
            return Vector2D(v.x * other, v.y * other)
        else:
            return Vector2D(v.x * other.x, v.y * other.y)
    
    def __init__(self, x:float, y:float):
        self.x = x
        self.y = y

    def tuple(self) -> tuple[float, float]:
        return (self.x, self.y)

    def length(self):
        return (self.x**2 + self.y**2)**(1/2)
    
    def copy(self):
        return Vector2D(self.x, self.y)
    
    #for ease of use
    def __add__(self, other:Vector2D) -> Vector2D:
        return Vector2D.add(self, other)
    
    def __sub__(self, other:Vector2D) -> Vector2D:
        return Vector2D.sub(self, other)
    
    def __mul__(self, other:int | float | Vector2D) -> Vector2D:
        return Vector2D.scale(self, other)
    
    def __rmul__(self, other:int | float | Vector2D) -> Vector2D:
        return self * other

    def __truediv__(self, other:int | float) -> Vector2D:
        return self * (1/other)
    
    #for debugging
    def __str__(self):
        return f"({self.x}, {self.y})"
