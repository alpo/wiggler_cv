from collections import namedtuple

import numpy as np
from scipy import optimize

Location1 = namedtuple('Location', ['coordinates', 'rotation_rad', 'scale', 'cost'])
Location2 = namedtuple('Location', ['coordinates', 'rotscale', 'cost'])


class Markers:
    marker_size = 15.
    marker_distance = 35.
    marker_ids = [42, 18, 12]

    marker_corners = np.array([
        [marker_size / 2, -marker_size / 2, 1],
        [marker_size / 2, marker_size / 2, 1],
        [-marker_size / 2, marker_size / 2, 1],
        [-marker_size / 2, -marker_size / 2, 1],
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
            c = c[0]
            i = i[0]
            if i in cls.markers:
                aligned_markers.append(cls.markers[i])
        a = np.array(aligned_markers)
        if a.shape == (0,):
            return None
        b = a.transpose((0, 2, 1))
        reference_corners = b.reshape((b.shape[0] * b.shape[1], 3)).T

        c = np.array(corners)
        c = c.squeeze(1)
        if c.shape[1] != 4 or c.shape[2] != 2:
            raise ValueError('Wrong corners dimension: {}. Must be (n,4,2)'.format(c.shape))
        d = c.reshape((b.shape[0] * b.shape[1], 2))
        input_corners = np.vstack((d.T, np.ones(d.shape[0])))

        position_guess = np.array([0., 0., 0., 1.])
        if False:
            opt_result = optimize.least_squares(cls.error_function, position_guess,
                                                args=(reference_corners, input_corners))
            position = Location1(coordinates=[opt_result.x[0], opt_result.x[1]],
                                 rotation_rad=opt_result.x[2],
                                 scale=opt_result.x[3],
                                 cost=opt_result.cost)
        else:
            A_matrix = []
            b_vector = []
            for col in range(input_corners.shape[1]):
                ic = input_corners[:, col]
                rc = reference_corners[:, col]
                A_matrix.append([1., 0., rc[0], -rc[1]])
                b_vector.append(ic[0])
                A_matrix.append([0., 1., rc[1], rc[0]])
                b_vector.append(ic[1])
            x, residuals, rank, s = np.linalg.lstsq(A_matrix, b_vector)
            position = Location2(coordinates=[x[0], x[1]],
                                 rotscale=[x[2], x[3]],
                                 cost=residuals[0])

        return position
