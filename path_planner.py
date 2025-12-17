# import shapely
import matplotlib
import math 


class LineMaker:
    @staticmethod
    def make_line_with_2_points(p1,p2):
        x1,y1 = p1
        x2,y2 = p2
        x= x1-x2
        y= y1-y2

        # y = mx + c 
        # y1 = x1 + c
        c = y1 - x1 
        m = y/x
        line = Line(m=m, c=c, p1=p1, p2=p2)
        return line
    
    @staticmethod
    def make_line_with_c_and_m(c,m):
        line = Line(m = m, c = c)
        return line
    
    @staticmethod
    def make_line_with_pg(p1,m):
        # y1 - y2 = m(x1-x2)
        # y = m(x1) - mx + y2 
        # y = -mx + (m(x1) + y2)
        c = (m*p1[0]) + p1[1]
        m = m * -1
        line = Line(m = m, c = c)
        return line
        

@dataclass
class Line:
    m: float
    c: float = 0
    p1: tuple = None
    p2: tuple = None
    traveled_to: bool = False

    def add_start_end_point(self,p1,p2):
        self.p1 = p1 
        self.p2 = p2

class PlotPoints:
    def __init__(self,scan_width,external_polygon):
        self.scan_width = scan_width
        self.external_polygon_lon_lat = external_polygon

        self.center_gps = self._center_of_poly(external_polygon)
        self.graident = self._find_palth_graident(external_polygon)

        # can use holes later 
        self.boundary_poly = self._convert_poly_to_shapely(external_polygon)

    def _convert_gps_to_rel(self,gps_point,poly_center): # -> point (x,y)
        lon, lat = gps_point
        lon0, lat0 = poly_center
        EARTH_RADIUS = 6371 * 1000

        x = math.radians((lon - lon0)) * (EARTH_RADIUS * math.cos(math.radians(lat0)))
        y = math.radians((lat - lat0)) * EARTH_RADIUS

        return (x, y)

    def _convert_rel_to_gps(self,rel_point,poly_center): # -> point (x,y)
        x, y = rel_point
        lon0, lat0 = poly_center
        EARTH_RADIUS = 6371 * 1000 

        # x = (lon - lon0) * (EARTH_RADIUS * math.cos(math.radians(lat0))) * (math.pi / 180)
        # y = (lat - lat0) * EARTH_RADIUS * (math.pi / 180)

        lon = x / (EARTH_RADIUS * math.cos(math.radians(lat0)))
        lat = y / EARTH_RADIUS
        lon = math.degrees(lon) + lon0
        lat = math.degrees(lat) + lat0

        return (lon,lat)

    def _center_of_poly(self,poly): # [(lon lat), ] -> (ave_lon,ave_lat)
        average_lon = 0
        average_lat = 0 
        sum_lon = 0
        sum_lat = 0 

        count = len(poly)

        for i in poly:
            sum_lon += i[0]
            sum_lat += i[1]

        ave_tuple = (sum_lon/count,sum_lat/count) 

        return ave_tuple
    
    def _convert_poly_to_rel(self,poly):
        center = self._center_of_poly(poly)
        rel_poly = []
        for i in poly:
            point = self._convert_gps_to_rel(i,center)
            rel_poly.append(point)


        rel_poly
        # return shapely.polygons(rel_poly)

    def _dist_between_points(self,p1,p2): # (x,y) -> dist in m
        x1,y1 = p1
        x2,y2 = p2
        x= x1-x2
        y= y1-y2

        dist = ((x)** 2 + (y)** 2)** 0.5
        return dist
    
    def _find_palth_graident(self,poly):
        max_dist = 0 
        points = [(0,0),(0,0)]

        for i in range(len(poly)):
            point1 = poly[i]
            point2 = poly[i+1]
            if max_dist <= (new_dist := self._dist_between_points(point1,point2)):
                max_dist = new_dist
                points = [point1,point2]
        
        # y = mx + c 
        # pg fomual is y1 - y2 = m(x1- x2)
        # m = (y1 - y2) / (x1 - x2)

        x1,y1 = point1
        x2,y2 = point2
        x= x1-x2
        y= y1-y2

        m = y/x

        return m 

    def _find_intersection_points(self,poly, line: Line): 
        # y = mx + c
        # m1x + c1 = m2x + c2 
        # m1x - m2x + c1 = c2 
        # x(m1 - m2) = (c2 - c1)
        # x = (c2 - c1) / (m1 - m2)
        # X = x 
        # y = m1(X) + c1
        # Y = m1((c2 - c1) / (m1 - m2)) + c1
        
        # line is 1
        # poly is 2
        intersection = []
        for i in poly:
            i = LineMaker.make_line_with_2_points(i)
            if i.m == line.m:
                continue
            x = (i.c - line.c) / (i.m - line.m) 
            y = (line.m * x) + line.c
            
            x_min = min(i.p1[0],i.p2[0])
            x_max = max(i.p1[0],i.p2[0])

            y_min = min(i.p1[1],i.p2[1])
            y_max = max(i.p1[1],i.p2[1])
            
            if x >= x_min and x <= x_max and y >= y_min and y <= y_max:
                point = (x,y)
                intersection.append(point)

        if len(intersection) % 2 != 0:
            raise ValueError("ther should be a even number of intersections")
        intersection = sorted(intersection, key =lambda i : i[0])
        
        if intersection == []:
            return None
        return intersection

    def _split_up_lines_by_intersections(self,poly,line: Line):
        intersection = self._find_intersection_points(poly,line)

        lines = []
        for i in range(len(intersection)):
            if i % 2 == 1:
                continue
            line = LineMaker(intersection[i],intersection[i+1])
            lines.append(line) 

        return lines

    def _make_lines(self,poly,scan_width=None):
        if not scan_width:
            scan_with = self.scan_width

        lines = []
        center = self._center_of_poly(poly)
        m = self.graident 

        center = self._center_of_poly(poly)
        m = self.graident 

        center_line = LineMaker.make_line_with_pg(p1=center,m=m)

        current_line = center_line
        while self._find_intersection_points(poly,current_line) != None:
            c = current_line.c + scan_width
            current_line = LineMaker.make_line_with_c_and_m(c=c,m=m)
            lines.append(current_line)

        while self._find_intersection_points(poly,current_line) != None:
            c = current_line.c - scan_width
            current_line = LineMaker.make_line_with_c_and_m(c=c,m=m)
            lines.append(current_line)
        
        return lines
