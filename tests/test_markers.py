from unittest import TestCase

from markers import Markers, Location1


class TestMarkers(TestCase):
    def test_get_location(self):
        corners = [
            [
                [
                    [1, -1], [1, 1], [-1, 1], [-1, -1]
                ]
            ]
        ]
        ids = [[x, ] for x in Markers.markers.keys()]
        position = Markers.get_location(corners, ids)
        print(position)
        if isinstance(position, Location1):
            self.assertAlmostEqual(position.coordinates[0] / position.scale, -Markers.marker_distance, places=2)
            self.assertAlmostEqual(position.coordinates[1], 0, places=2)
            self.assertAlmostEqual(position.rotation_rad, 0, places=2)
            self.assertAlmostEqual(position.scale, 2 / Markers.marker_size, places=2)
            self.assertAlmostEqual(position.cost, 0, places=2)
        else:
            self.assertAlmostEqual(position.coordinates[0] / position.rotscale[0], -Markers.marker_distance, places=2)
            self.assertAlmostEqual(position.coordinates[1], 0, places=2)
            self.assertAlmostEqual(position.rotscale[1], 0, places=2)
            self.assertAlmostEqual(position.rotscale[0], 2 / Markers.marker_size, places=2)
            self.assertAlmostEqual(position.cost, 0, places=2)

    def test_get_location_cost(self):
        corners = [
            [
                [
                    [1.2, -1], [1.2, 1], [-0.8, 1], [-0.8, -1]
                ],
            ],
            [
                [
                    [0.8, -1], [0.8, 1], [-1.2, 1], [-1.2, -1]
                ],
            ]
        ]
        ids = [[list(Markers.markers.keys())[0], ], ] * 2
        position = Markers.get_location(corners, ids)
        print(position)
        if isinstance(position, Location1):
            self.assertAlmostEqual(position.coordinates[0] / position.scale, -Markers.marker_distance, places=2)
            self.assertAlmostEqual(position.coordinates[1], 0, places=2)
            self.assertAlmostEqual(position.rotation_rad, 0, places=2)
            self.assertAlmostEqual(position.scale, 2 / Markers.marker_size, places=2)
            self.assertAlmostEqual(position.cost, 0, places=2)
        else:
            self.assertAlmostEqual(position.coordinates[0] / position.rotscale[0], -Markers.marker_distance, places=2)
            self.assertAlmostEqual(position.coordinates[1], 0, places=2)
            self.assertAlmostEqual(position.rotscale[1], 0, places=2)
            self.assertAlmostEqual(position.rotscale[0], 2 / Markers.marker_size, places=2)
            self.assertAlmostEqual(position.cost, 0.32, places=2)
