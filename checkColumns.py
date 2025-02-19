import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Polygon, Point
 
def find_intersection_ratio(input_point, curve_points):
    """
    Finds the intersection of a line from the origin through the input point with a closed polygon
    and returns the ratio of distances (origin to input point) / (origin to intersection).
 
    Parameters:
    input_point (tuple): The (x, y) coordinates of the input point.
    curve_points (list of tuples): A list of (x, y) points forming a closed polygon.
 
    Returns:
    float: Ratio of distance to input point to distance to polygon intersection.
    """
    # Define the polygon
    polygon = Polygon(curve_points)
    # Create a line from the origin through the input point extending outward
    x, y = input_point
    direction = np.array([x, y])
    direction = direction / np.linalg.norm(direction)  # Normalize direction
    extended_point = direction * 1000  # Large value to ensure it intersects
    # Define the line
    origin = (0, 0)
    ray = LineString([origin, (extended_point[0], extended_point[1])])
 
    # Find the intersection with the polygon
    intersection = polygon.exterior.intersection(ray)
 
    # Handle case where there's no intersection
    if intersection.is_empty:
        return None  # No valid ratio if there's no intersection
    # If multiple intersection points exist, take the closest one
    if intersection.geom_type == "MultiPoint":
        intersection = min(intersection.geoms, key=lambda p: Point(origin).distance(p))
    intersection_point = (intersection.x, intersection.y)
    # Compute distances
    distance_to_input = np.linalg.norm([x, y])
    distance_to_polygon = np.linalg.norm([intersection.x, intersection.y])
    # Compute the ratio
    ratio = distance_to_input / distance_to_polygon
    print("Intersection Point:", intersection_point)
    print("Distance to Input Point:", distance_to_input)
    print("Distance to Intersection Point:", distance_to_polygon)
    print("Ratio:", ratio)
 
    # Visualization
    plt.figure(figsize=(6,6))
    plt.plot(*zip(*curve_points, curve_points[0]), 'b-', label="Polygon")  # Closed polygon
    plt.plot([0, x], [0, y], 'g--', label="Ray to Input Point")  # Line to input
    plt.plot([0, intersection.x], [0, intersection.y], 'r-', label="Ray to Polygon")  # Line to polygon
    plt.scatter(*input_point, color='g', label="Input Point")
    plt.scatter(*intersection_point, color='r', label="Intersection Point")
    plt.scatter(0, 0, color='black', label="Origin")
    plt.legend()
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")
    plt.title("Intersection of Ray with Polygon")
    plt.grid()
    plt.show()
 
    return ratio
 
# Example Usage
curve_pts = [(6, 3), (2,4),(-6, 3), (-6, -3), (6, -3)]
input_pt = (-3, -2)
 
ratio = find_intersection_ratio(input_pt, curve_pts)
print("Ratio:", ratio)