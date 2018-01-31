from collections import namedtuple

import numpy as np
from scipy import optimize

Location = namedtuple('Location', ['coordinates', 'rotation_rad', 'scale', 'cost'])


class Markers:
    marker_size = 15.
    marker_distance = 30.
    marker_ids = [42, 11, 34]

    marker_corners = np.array([
        [marker_size / 2, marker_size / 2, 1],
        [marker_size / 2, -marker_size / 2, 1],
        [-marker_size / 2, -marker_size / 2, 1],
        [-marker_size / 2, marker_size / 2, 1],
    ]).transpose()

    angle = 120. / 180. * np.pi
    translation = np.array([
        [1, 0, marker_distance],
        [0, 1, 0],
        [0, 0, 1]
    ])
    rotation = np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
    ])
    markers = dict(zip(marker_ids, [np.dot(translation, marker_corners),
                                    np.dot(np.dot(rotation, translation), marker_corners),
                                    np.dot(np.dot(np.dot(rotation, rotation), translation), marker_corners)
                                    ]))

    @classmethod
    def error_function(cls, position, reference_corners, input_corners):
        x, y, angle, scale = list(position)
        affine_transform = np.array([
            [scale * np.cos(angle), -scale * np.sin(angle), x],
            [scale * np.sin(angle), scale * np.cos(angle), y],
            [0, 0, 1]
        ])
        moved_corners = np.dot(affine_transform, reference_corners)
        diffs = input_corners - moved_corners
        r_diffs = np.square(diffs[0, :]) + np.square(diffs[1, :])
        return r_diffs

    @classmethod
    def get_location(cls, corners, ids):
        aligned_markers = []
        for c, i in zip(corners, ids):
            aligned_markers.append(cls.markers[i])
        a = np.array(aligned_markers)
        b = a.transpose((0, 2, 1))
        reference_corners = b.reshape((b.shape[0] * b.shape[1], 3)).T

        c = np.array(corners)
        if c.shape[1] != 4 or c.shape[2] != 2:
            raise ValueError('Wrong corners dimension: {}. Must be (n,4,2)'.format(c.shape))
        d = c.reshape((b.shape[0] * b.shape[1], 2))
        input_corners = np.vstack((d.T, np.ones(d.shape[0])))

        position_guess = np.array([0., 0., 0., 1.])
        opt_result = optimize.least_squares(cls.error_function, position_guess,
                                            args=(reference_corners, input_corners))
        position = Location(coordinates=[opt_result.x[0], opt_result.x[1]],
                            rotation_rad=opt_result.x[2],
                            scale=opt_result.x[3],
                            cost=opt_result.cost)
        return position
