# import shapely
import math
from dataclasses import dataclass
from typing import Optional


class LineMaker:
    line_dir: int = 1
    
    @staticmethod
    def make_line_with_2_points(p1: tuple[float, float], p2: tuple[float, float]) -> 'Line':
        x1, y1 = p1
        x2, y2 = p2
        x = x1 - x2
        y = y1 - y2

        # y = mx + c 
        # y1 = x1 + c
        try:
            m = y / x
        except ZeroDivisionError:
            m = y / (x + 0.0000000000000000000000001)
        c = y1 - m * x1 
        if LineMaker.line_dir == 1:
            line = Line(m=m, c=c, p1=p1, p2=p2)
        else: 
            line = Line(m=m, c=c, p1=p2, p2=p1)
        LineMaker.line_dir *= -1
        return line
    
    @staticmethod
    def make_line_with_c_and_m(c: float, m: float) -> 'Line':
        line = Line(m=m, c=c)
        return line
    
    @staticmethod
    def make_line_with_pg(p1: tuple[float, float], m: float) -> 'Line':
        # y1 - y2 = m(x1-x2):
        # y = m(x1) - mx + y2 
        # y = -mx + (m(x1) + y2)
        c = (m * p1[0]) + p1[1]
        m = m * -1
        line = Line(m=m, c=c)
        return line
        
@dataclass
class Line:
    m: float
    c: float = 0
    p1: Optional[tuple[float, float]] = None
    p2: Optional[tuple[float, float]] = None
    traveled_to: bool = False

    def add_start_end_point(self, p1: tuple[float, float], p2: tuple[float, float]) -> None:
        self.p1 = p1 
        self.p2 = p2

class CPP:
    def __init__(self, scan_width: float, external_polygon: list[list[float]], home_lon_lat: Optional[list[float]] = None) -> None:
        if home_lon_lat == None:
            home_lon_lat = external_polygon[0]
        self.scan_width: float = scan_width
        self.external_polygon_lon_lat: list[list[float]] = external_polygon
        self.graident: float = self._find_palth_graident(external_polygon)

        # can use holes later 
        self.boundary_poly: list[tuple[float, float]] = self._convert_poly_to_rel(external_polygon)

    def _convert_gps_to_rel(self, gps_point: list[float], poly_center: list[float]) -> tuple[float, float]:  # -> point (x,y)
        lon, lat = gps_point
        lon0, lat0 = poly_center
        EARTH_RADIUS = 6371 * 1000

        x = math.radians((lon - lon0)) * (EARTH_RADIUS * math.cos(math.radians(lat0)))
        y = math.radians((lat - lat0)) * EARTH_RADIUS

        return (x, y)

    def _convert_rel_to_gps(self, rel_point: tuple[float, float], poly_center: tuple[float, float]) -> tuple[float, float]:  # -> point (x,y)
        x, y = rel_point
        lon0, lat0 = poly_center
        EARTH_RADIUS = 6371 * 1000 

        # x = (lon - lon0) * (EARTH_RADIUS * math.cos(math.radians(lat0))) * (math.pi / 180)
        # y = (lat - lat0) * EARTH_RADIUS * (math.pi / 180)

        lon = x / (EARTH_RADIUS * math.cos(math.radians(lat0)))
        lat = y / EARTH_RADIUS
        lon = math.degrees(lon) + lon0
        lat = math.degrees(lat) + lat0

        return (lon, lat)

    def _center_of_poly(self, poly: list) -> tuple[float, float]:  # [(lon lat), ] -> (ave_lon,ave_lat)
        average_lon = 0
        average_lat = 0 
        sum_lon = 0
        sum_lat = 0 

        count = len(poly)

        for i in poly:
            sum_lon += i[0]
            sum_lat += i[1]

        ave_tuple = (sum_lon / count, sum_lat / count) 

        return ave_tuple
    
    def _convert_poly_to_rel(self, poly: list[list[float]]) -> list[tuple[float, float]]:
        center = self._center_of_poly(poly)
        rel_poly = []
        for i in poly:
            point = self._convert_gps_to_rel(i, center)
            rel_poly.append(point)

        return rel_poly
        # return shapely.polygons(rel_poly)

    def _convert_rel_poly_to_gps(self, poly: list[tuple[float, float]]) -> list[tuple[float, float]]:
        center = self._center_of_poly(poly)
        rel_poly = []
        for i in poly:
            point = self._convert_rel_to_gps(i, center)
            rel_poly.append(point)

        return rel_poly

    def _dist_between_points(self, p1: tuple[float, float], p2: tuple[float, float]) -> float:  # (x,y) -> dist in m
        x1, y1 = p1
        x2, y2 = p2
        x = x1 - x2
        y = y1 - y2

        dist = ((x) ** 2 + (y) ** 2) ** 0.5
        return dist
    
    def _find_palth_graident(self, poly: list[list[float]]) -> float:
        max_dist = 0 
        points = [(0, 0), (0, 0)]

        for i in range(len(poly) - 1):
            point1 = poly[i]
            point2 = poly[i + 1]
            if max_dist <= (new_dist := self._dist_between_points(point1, point2)):
                max_dist = new_dist
                points = [point1, point2]
        
        # y = mx + c 
        # pg fomual is y1 - y2 = m(x1- x2)
        # m = (y1 - y2) / (x1 - x2)

        x1, y1 = point1
        x2, y2 = point2
        x = x1 - x2
        y = y1 - y2

        m = y / x

        return m 

    def _find_intersection_points(self, poly: list[tuple[float, float]], line: Line) -> list[tuple[float, float]]: 
        poly = poly + [poly[0]]
        # print(poly)
        intersection_points = []
        for i in range(len(poly) - 1):
            p1 = poly[i]
            p2 = poly[i + 1]
            # print(p1,p2)
            poly_line = LineMaker.make_line_with_2_points(p1, p2)

            c1, m1 = line.c, line.m
            c2, m2 = poly_line.c, poly_line.m
            m1 = line.m

            if abs(m1 - m2) < 1e-9:
                continue

            x = (c2 - c1) / (m1 - m2)
            y = m1 * (x) + c1

            point = (x, y)

            fpe = 1e-9 
            x_max = max(poly_line.p1[0], poly_line.p2[0]) + fpe
            x_min = min(poly_line.p1[0], poly_line.p2[0]) - fpe

            y_max = max(poly_line.p1[1], poly_line.p2[1]) + fpe
            y_min = min(poly_line.p1[1], poly_line.p2[1]) - fpe

            x_check = x_min <= x <= x_max
            y_check = y_min <= y <= y_max
            if x_check and y_check:
                intersection_points.append((x, y))

        # if intersection_points == []:
        #     raise ValueError("should not be none") 

        if len(intersection_points) % 2 == 0:
            sort_points = []
            intersection_points.sort(key=lambda p: (p[0], p[1]))  # or along your scan direction
            for p1, p2 in zip(intersection_points[0::2], intersection_points[1::2]):
                sort_points.append((p1, p2))
        else:
            raise ValueError("should have retuned a even number")

        return intersection_points
        
    def _split_up_lines_by_intersections(self, poly: list[tuple[float, float]], line: Line) -> list[Line]:
        intersection = self._find_intersection_points(poly, line)

        lines = []
        for i in range(len(intersection)):
            if i % 2 == 1:
                continue
            line = LineMaker.make_line_with_2_points(intersection[i], intersection[i + 1])
            lines.append(line) 

        return lines

    def _make_lines(self, poly: list[tuple[float, float]], scan_width: Optional[float] = None) -> list[Line]:
        if not scan_width:
            scan_width = self.scan_width

        lines = []
        center = self._center_of_poly(poly)
        m = self.graident 

        # center = self._center_of_poly(poly)

        # center_line = LineMaker.make_line_with_pg(p1=center,m=m*-1)
        # lines.append(center_line)
        for j in [1, -1]:
            current_line = LineMaker.make_line_with_pg(center, m)
            c = current_line.c
            while True:
                current_line = LineMaker.make_line_with_c_and_m(c=c, m=m)

                # print(self._find_intersection_points(poly,current_line))

                if self._find_intersection_points(poly, current_line) != []:
                    new_lines = self._split_up_lines_by_intersections(poly, current_line) 
                    for i in new_lines:
                        lines.append(i)
                        current_line = i 
                    c = c - (scan_width) * j

                else: break
            # if j == 1:
                # lines = lines[::-1] # to make the lines go all in the same direction
        return lines 

    def genarate_scan_palth(self, poly: list[list[float]], scan_width: float) -> tuple[list[tuple[float, float]], list[Line]]:
        lon_lat_poly = poly
        poly = self._convert_poly_to_rel(poly)
        lines = self._make_lines(poly, scan_width)
        new_lines = [] 
        for i in lines:
            try:
                # print(i)
                new_lines.append(i.p1)
                new_lines.append(i.p2)
            except TypeError:
                pass

        return poly, lines

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from adjustText import adjust_text

    def plot_scan_paths(polygon: list[tuple[float, float]], lines: list[Line], extend_factor: float = 2.0, polygon_color: str = 'k', line_color: str = 'r') -> None:
        # Plot the polygon
        poly_x = [p[0] for p in polygon] + [polygon[0][0]]
        poly_y = [p[1] for p in polygon] + [polygon[0][1]]
        plt.plot(poly_x, poly_y, f'{polygon_color}-', linewidth=2, label='Polygon')

        point_count = 0
        text_array = []
        for line in lines[::-1]:
            """
            make points 
            lable poiints and plot tyhem 
            """
            points = line.p1, line.p2
            x, y = list(zip(*points))
            plt.plot(x, y)
            for i in points:
                point_count += 1
                # text = plt.annotate(str(point_count), (i[0], i[1]), textcoords="offset points", xytext=(5, 5),fontsize=10, color='blue') 
                plt.plot(i[0], i[1], 'ro', markersize=4, zorder=5)
                plt.annotate(str(point_count), i, 
                     xytext=(25, 25), textcoords='offset points',
                     fontsize=8, color='blue', fontweight='bold',
                     bbox=dict(boxstyle='round,pad=0.3', 
                              facecolor='yellow', alpha=0.8),
                     arrowprops=dict(arrowstyle='->', 
                                    color='blue', 
                                    lw=1),
                     zorder=10)
        
        plt.gca().set_aspect('equal', adjustable='box')
        plt.xlabel('X (m)')
        plt.ylabel('Y (m)')
        plt.title('Polygon with Scan Lines')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.show()

    


    test_data = {
    "timestamp": "20251216_180012",
    "boundary": [
        [
        -35.353793628499425,
        149.16532516479495
        ],
        [
        -35.35634869955396,
        149.1591024398804
        ],
        [
        -35.35865869421017,
        149.15627002716067
        ],
        [
        -35.360933624359085,
        149.1567420959473
        ],
        [
        -35.36317349295723,
        149.16139841079715
        ],
        [
        -35.364905848708105,
        149.1684150695801
        ],
        [
        -35.364975842098524,
        149.1697669029236
        ],
        [
        -35.362508538452815,
        149.17315721511844
        ],
        [
        -35.35780120390604,
        149.17667627334598
        ],
        [
        -35.353863631523176,
        149.17785644531253
        ],
        [
        -35.35284858173993,
        149.17564630508426
        ],
        [
        -35.35500117215463,
        149.17362928390506
        ],
        [
        -35.35937617909993,
        149.17384386062625
        ],
        [
        -35.361073617967,
        149.17201995849612
        ],
        [
        -35.36186107748863,
        149.16646242141726
        ],
        [
        -35.36137110357785,
        149.162814617157
        ],
        [
        -35.35946367682106,
        149.16238546371463
        ],
        [
        -35.358186783792384,
        149.1668594529933
        ],
        [
        -35.35890368976739,
        149.17000293731692
        ],
        [
        -35.356068695711336,
        149.17103290557864
        ],
        [
        -35.3524460584657,
        149.17017459869388
        ],
        [
        -35.35137848702254,
        149.1681790351868
        ],
        [
        -35.35192102509314,
        149.1659474372864
        ],
        [
        -35.35234105206425,
        149.16277170181277
        ],
        [
        -35.35363612147413,
        149.15766477584842
        ],
        [
        -35.35561368739635,
        149.15431737899783
        ],
        [
        -35.35664620257297,
        149.15345907211307
        ],
        [
        -35.35627869868433,
        149.15622711181643
        ],
        [
        -35.35424864706918,
        149.1586518287659
        ],
        [
        -35.35302359123341,
        149.1624712944031
        ],
        [
        -35.352533563695985,
        149.16566848754886
        ],
        [
        -35.353723625414986,
        149.16708469390872
        ],
        [
        -35.355298680138,
        149.16744947433475
        ],
        [
        -35.3544936560064,
        149.165153503418
        ]
    ],
    "obstacles": [],
    "scan_spacing": 25,
    "altitude": 20
    }

    obj = CPP(scan_width=1, external_polygon=test_data['boundary'])
    palth = obj.genarate_scan_palth(test_data['boundary'], scan_width=300)

    plot_scan_paths(palth[0], palth[1])