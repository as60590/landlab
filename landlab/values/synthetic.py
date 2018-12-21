"""
synthetic.py provides functions to add synthetic values to a model grid.

Values can be added to any valid grid element (e.g. link or node). If no field
exists, a field of float zeros will be initialized.

All functions add values to the field---this means that multiple functions can
be chained together.

All functions support adding values to only portions of the grid, based on the
``status_at_link`` and ``status_at_node`` attributes.

For example, if one wanted to construct an initial topographic elevation
represented by a tetrahedron and add normally distributed noise only to core
nodes, this could be acomplished as follows:

Examples
--------
>>> import numpy as np
>>> from landlab import RasterModelGrid
>>> from landlab import CORE_NODE
>>> from landlab.values import random_normal, plane
>>> mg = RasterModelGrid((11, 11))

"""
import numpy as np


def _create_missing_field(grid, name, at):
    """Create field of zeros if missing."""
    if name not in grid[at]:
        grid.add_zeros(at, name)


def _where_to_add_values(grid, at, status):
    "Determine where to put values."
    where = np.zeros(grid.size(at), dtype=bool)
    if at is "link":
        status_values = grid.status_at_link
    elif at is "node":
        status_values = grid.status_at_node
    else:
        if status is not None:
            raise ValueError(("No status information exists for grid elements "
                              "that are not nodes or links."))

    # based on status, set where to true. support value or iterable.
    if status is None:
        where = np.ones(grid.size(at), dtype=bool)
    else:
        try:
            for s in status:
                where[status_values == s] = True
        except TypeError:
            where[status_values == status] = True

    return where


def random_uniform(grid, name, at='node', status=None, **kwargs):
    """Add uniform noise to a grid.

    Parameters
    ----------
    grid : ModelGrid
    name : str
        Name of the field.
    at : str, optional
        Grid location to store values. If not given, values are
        assumed to be on `node`.
    status : status-at-grid-element or list, optional
        A value or list of the grid element status at which values
        are added. By default, values are added to all elements.
    kwargs : dict
        Keyword arguments to pass to ``np.random.uniform``.

    Returns
    -------
    values : array
        Array of the values added to the field.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab import RasterModelGrid
    >>> from landlab import CORE_NODE
    >>> from landlab.values import random_uniform
    >>> np.random.seed(42)
    >>> mg = RasterModelGrid((4, 4))
    >>> values = random_uniform(mg,
    ...                         'soil__depth',
    ...                         'node',
    ...                         status=CORE_NODE,
    ...                         high=3.,
    ...                         low=2.)
    >>> mg.at_node['soil__depth']
    array([ 0.        ,  0.        ,  0.        ,  0.        ,
            0.        ,  2.37454012,  2.95071431,  0.        ,
            0.        ,  2.73199394,  2.59865848,  0.        ,
            0.        ,  0.        ,  0.        ,  0.        ])
    """
    where = _where_to_add_values(grid, at, status)
    _create_missing_field(grid, name, at)
    values = np.zeros(grid.size(at))
    values[where] += np.random.uniform(size=np.sum(where), **kwargs)
    grid[at][name][:] += values
    return values


def random_normal(grid, name, at, status=None, **kwargs):
    """Add normally distributed noise to a grid.

    Parameters
    ----------
    grid : ModelGrid
    name : str
        Name of the field.
    at : str, optional
        Grid location to store values. If not given, values are
        assumed to be on `node`.
    status : status-at-grid-element or list, optional
        A value or list of the grid element status at which values
        are added. By default, values are added to all elements.
    kwargs : dict
        Keyword arguments to pass to ``np.random.normal``.

    Returns
    -------
    values : array
        Array of the values added to the field.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab import RasterModelGrid
    >>> from landlab.values import random_normal
    >>> np.random.seed(42)
    >>> mg = RasterModelGrid((4, 4))
    >>> values = random_normal(mg,
    ...                        'soil__depth',
    ...                        'node',
    ...                        loc=5.,
    ...                        scale=1.)
    >>> mg.at_node['soil__depth']
    array([ 5.49671415,  4.8617357 ,  5.64768854,  6.52302986,
            4.76584663,  4.76586304,  6.57921282,  5.76743473,
            4.53052561,  5.54256004,  4.53658231,  4.53427025,
            5.24196227,  3.08671976,  3.27508217,  4.43771247])
    """
    where = _where_to_add_values(grid, at, status)
    _create_missing_field(grid, name, at)
    values = np.zeros(grid.size(at))
    values[where] += np.random.normal(size=np.sum(where), **kwargs)
    grid[at][name][:] += values
    return values


def plane(grid, name, at, status=None, point=(0., 0., 0), normal=(0., 0., 1.)):
    """Add a single plane defined by a point and a normal to a grid.

    Parameters
    ----------
    grid : ModelGrid
    name : str
        Name of the field.
    at : str, optional
        Grid location to store values. If not given, values are
        assumed to be on `node`.
    status : status-at-grid-element or list, optional
        A value or list of the grid element status at which values
        are added. By default, values are added to all elements.
    point : tuple, optional
        A tuple defining a point the plane goes through in the
        format (x, y, z). Default is (0., 0., 0.)
    normal : tuple, optional
        A tuple defining the normal to the plane in the format
        (dx, dy, dz). Must not be verticaly oriented. Default
        is a horizontal plane (0., 0., 1.).

    Returns
    -------
    values : array
        Array of the values added to the field.

    Examples
    --------
    >>> from landlab import RasterModelGrid
    >>> from landlab.values import plane
    >>> mg = RasterModelGrid((4, 4))
    >>> values = plane(mg,
    ...                'soil__depth',
    ...                'node',
    ...                point=(0., 0., 0.),
    ...                normal=(-1., -1., 1.))
    >>> mg.at_node['soil__depth']
    array([ 0.,  1.,  2.,  3.,
            1.,  2.,  3.,  4.,
            2.,  3.,  4.,  5.,
            3.,  4.,  5.,  6.])

    """
    if np.isclose(normal[2], 0):
        raise ValueError("")
    where = _where_to_add_values(grid, at, status)
    _create_missing_field(grid, name, at)
    grid[at][name][where] += _plane_function(grid, at, point, normal)[where]
    return plane


def _plane_function(grid, at, point, normal):
    """calculate the plane function"""
    if np.isclose(normal[2], 0):
        raise ValueError("")

    if at is "node":
        x = grid.x_of_node
        y = grid.y_of_node
    elif at is "link":
        x = grid.x_of_link
        y = grid.y_of_link
    elif at is "cell":
        x = grid.x_of_cell
        y = grid.y_of_cell
    elif at is "face":
        x = grid.x_of_face
        y = grid.y_of_face
    else:
        raise ValueError("")

    constant = (point[0] * normal[0] +
                point[1] * normal[1] +
                point[2] * normal[2])
    values = ((constant
              - (normal[0] * (x - point[0]))
              - (normal[1] * (y - point[1])))
             / normal[2])
    return values


def multipy_planes(grid, name, at,
                   status=None,
                   planes=[]):
    """Add multiple planes multiplied together.

    Parameters
    ----------
    grid : ModelGrid
    name : str
        Name of the field.
    at : str, optional
        Grid location to store values. If not given, values are
        assumed to be on `node`.
    status : status-at-grid-element or list, optional
        A value or list of the grid element status at which values
        are added. By default, values are added to all elements.
    planes :

    Returns
    -------
    values : array
        Array of the values added to the field.

    Examples
    --------
    >>> from landlab import RasterModelGrid
    >>> from landlab.values import multipy_planes
    >>> mg = RasterModelGrid((5, 5))
    >>> planes = [[(0,  0, 0), (0, -1, 1)],
    ...           [(0,  4, 0), (0,  1, 1)]]
    >>> values = multipy_planes(mg,
    ...                         'soil__depth',
    ...                         'node',
    ...                         planes=planes)
    >>> mg.at_node['soil__depth']
    array([ 0.,  1.,  2.,  3.,
            1.,  2.,  3.,  4.,
            2.,  3.,  4.,  5.,
            3.,  4.,  5.,  6.])

    """
    where = _where_to_add_values(grid, at, status)
    _create_missing_field(grid, name, at)

    field = np.ones(where.shape)
    for params in planes:
        field *= _plane_function(grid, at, params[0], params[1])

    grid[at][name][where] += field[where]
    return field


def constant(grid, name, at, status=None, constant=0.):
    """Add a constant to a grid.

    Parameters
    ----------
    grid : ModelGrid
    name : str
        Name of the field.
    at : str, optional
        Grid location to store values. If not given, values are
        assumed to be on `node`.
    status : status-at-grid-element or list, optional
        A value or list of the grid element status at which values
        are added. By default, values are added to all elements.
    constant : float, optional
        Constant value to add to the grid. Default is 0.

    Returns
    -------
    values : array
        Array of the values added to the field.

    Examples
    --------
    >>> from landlab import RasterModelGrid
    >>> from landlab import ACTIVE_LINK
    >>> from landlab.values import constant
    >>> mg = RasterModelGrid((4, 4))
    >>> values = constant(mg,
    ...                  'some_flux',
    ...                  'link',
    ...                  status=ACTIVE_LINK,
    ...                  constant=10)
    >>> mg.at_link['some_flux']
    array([  0.,   0.,   0.,   0.,  10.,  10.,   0.,  10.,  10.,  10.,   0.,
            10.,  10.,   0.,  10.,  10.,  10.,   0.,  10.,  10.,   0.,   0.,
             0.,   0.])

    """
    where = _where_to_add_values(grid, at, status)
    _create_missing_field(grid, name, at)
    values = np.zeros(grid.size(at))
    values[where] += constant
    grid[at][name][:] += values
    return values