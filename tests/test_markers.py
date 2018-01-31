from unittest import TestCase

from markers import Markers


class TestMarkers(TestCase):
    def test_get_location(self):
        corners = [
            [
                [1, 1], [1, -1], [-1, -1], [-1, 1]
            ]
        ]
        ids = list(Markers.markers.keys())
        position = Markers.get_location(corners, ids)
        self.assertAlmostEqual(position.coordinates[0] / position.scale, -Markers.marker_distance, places=2)
        self.assertAlmostEqual(position.coordinates[1], 0, places=2)
        self.assertAlmostEqual(position.rotation_rad, 0, places=2)
        self.assertAlmostEqual(position.scale, 2 / Markers.marker_size, places=2)
        self.assertAlmostEqual(position.cost, 0, places=2)
        print(position)

    # def test_get_location1(self):
    #     corners = list(Markers.markers.values())
    #     corners = np.array(corners)
    #     ids = list(Markers.markers.keys())
    #     position = Markers.get_location(corners, ids)
    #     print(position)
