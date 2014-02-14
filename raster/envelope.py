# pylint: disable=too-many-arguments,too-many-return-statements
# pylint: disable=arguments-differ

"""
Spatial envelope classes used mostly with raster data to determine extents
and snapping
"""

import math
import decimal
import copy

PRECISION = 0.0000001


class EnvelopeError(Exception):
    """
    Specialized exception to throw
    """
    pass


class Envelope(object):
    """
    An Envelope is a rectilinear set of coordinates that typically define
    the extent or bounds of spatial data.  This class provides other
    methods for comparison, union and intersection
    """

    def __init__(self, x_min, y_min, x_max, y_max):
        """
        Initialize an Envelope instance with bounding coordinates.  Raises
        an exception if passed coordinates do not form a valid envelope.

        Parameters
        ----------
        x_min : double
            Minimum x coordinate

        y_min : double
            Minimum y coordinate

        x_max : double
            Maximum x coordinate

        y_max : double
            Maximum y coordinate
        """
        self._x_min = x_min
        self._y_min = y_min
        self._x_max = x_max
        self._y_max = y_max

        try:
            self._assert_valid_envelope()
        except AssertionError:
            err_str = 'Invalid envelope shape'
            raise EnvelopeError(err_str)

    def __repr__(self):
        """
        Pretty print an Envelope instance
        """
        return "%s%r" % (self.__class__.__name__, tuple((self.x_min,
            self.y_min, self.x_max, self.y_max)))

    def __eq__(self, right):
        """
        Equality operator which is a simple check of self and other dicts
        """
        return self.__dict__ == right.__dict__

    # Simple properties to return class attributes
    # pylint: disable=missing-docstring
    @property
    def x_min(self):
        return self._x_min

    @property
    def y_min(self):
        return self._y_min

    @property
    def x_max(self):
        return self._x_max

    @property
    def y_max(self):
        return self._y_max
    # pylint: enable=missing-docstring

    def _assert_valid_envelope(self):
        """
        Ensure that this is a valid envelope by running comparison tests
        on bounding coordinates
        """
        assert self.x_min < self.x_max
        assert self.y_min < self.y_max

    def is_subset(self, other):
        """
        Method to test whether self is a subset of other (allowed to
        be coincident)
        """
        if self.x_min < other.x_min:
            return False
        if self.x_max > other.x_max:
            return False
        if self.y_min < other.y_min:
            return False
        if self.y_max > other.y_max:
            return False
        return True

    def is_superset(self, other):
        """
        Operator to test whether self is a superset of other (allowed to
        be coincident)
        """
        if self.x_min > other.x_min:
            return False
        if self.x_max < other.x_max:
            return False
        if self.y_min > other.y_min:
            return False
        if self.y_max < other.y_max:
            return False
        return True

    def is_disjoint(self, other):
        """
        Tests whether self and other are disjoint (non-overlapping)
        """
        if self.x_min > other.x_max:
            return True
        if self.x_max < other.x_min:
            return True
        if self.y_min > other.y_max:
            return True
        if self.y_max < other.y_min:
            return True
        return False

    def union(self, other):
        """
        Union method.  Returns the minimum bounding envelope of both self
        and other
        """
        x_min = min(self.x_min, other.x_min)
        y_min = min(self.y_min, other.y_min)
        x_max = max(self.x_max, other.x_max)
        y_max = max(self.y_max, other.y_max)
        return Envelope(x_min, y_min, x_max, y_max)

    def intersection(self, other):
        """
        Intersection method.  Returns the minimum bounding envelope of the
        overlap area of self and other
        """
        x_min = max(self.x_min, other.x_min)
        y_min = max(self.y_min, other.y_min)
        x_max = min(self.x_max, other.x_max)
        y_max = min(self.y_max, other.y_max)
        return Envelope(x_min, y_min, x_max, y_max)


class RasterEnvelope(Envelope):
    """
    A RasterEnvelope is an Envelope that also defines a cell size.  As such,
    it has the concept of x_size (number of columns) and y_size (number of
    rows).  It also enforces that the bounding envelope is a multiple of
    the cell size.
    """

    def __init__(self, x_min, y_min, x_max, y_max, cell_size):
        """
        Initialize a RasterEnvelope instance with bounding coordinates and a
        cell size. If the passed coordinates are not a multiple of cell size,
        the envelope is expanded to meet this requirement.

        Parameters
        ----------
        x_min : double
            Minimum x coordinate

        y_min : double
            Minimum y coordinate

        x_max : double
            Maximum x coordinate

        y_max : double
            Maximum y coordinate

        cell_size : double
            Cell size within envelope
        """
        # Call the Envelope superclass to set the initial envelope
        super(RasterEnvelope, self).__init__(x_min, y_min, x_max, y_max)
        self._cell_size = cell_size

        # Adjust the window if necessary
        self._x_max, self._y_min, self._x_size, self._y_size = \
            calculate_snapped_window(self, self.cell_size)

    def __repr__(self):
        """
        Pretty print a RasterEnvelope instance
        """
        return "%s(%.1f, %.1f, %.1f, %.1f, %.1f)" % (self.__class__.__name__,
            self.x_min, self.y_min, self.x_max, self.y_max,
            self.cell_size)

    def __eq__(self, other):
        """
        Equality operator.  Allows for tiny differences in coordinates due
        to floating-point precision
        """
        if math.fabs(self.x_min - other.x_min) > PRECISION:
            return False
        if math.fabs(self.y_min - other.y_min) > PRECISION:
            return False
        if math.fabs(self.x_min - other.x_min) > PRECISION:
            return False
        if math.fabs(self.x_min - other.x_min) > PRECISION:
            return False
        if math.fabs(self.cell_size - other.cell_size) > PRECISION:
            return False
        if self.x_size != other.x_size:
            return False
        if self.y_size != other.y_size:
            return False
        return True

    @classmethod
    def from_gdal_dataset(cls, ds):
        """
        Create a RasterEnvelope instance from a gdal.Dataset

        Parameters
        ----------
        ds : gdal.Dataset
            The input dataset from which to get the envelope
        """
        gt = ds.GetGeoTransform()
        x_min, y_max, cell_size = gt[0], gt[3], gt[1]
        x_max = x_min + (ds.RasterXSize * cell_size)
        y_min = y_max - (ds.RasterYSize * cell_size)
        return cls(x_min, y_min, x_max, y_max, cell_size)

    # Simple properties to return class attributes
    # pylint: disable=missing-docstring
    @property
    def x_size(self):
        return self._x_size

    @property
    def y_size(self):
        return self._y_size

    @property
    def cell_size(self):
        return self._cell_size
    # pylint: enable=missing-docstring

    def is_snapped(self, other):
        """
        Tests whether self and other are snapped (or aligned)
        """
        if self.cell_size != other.cell_size:
            return False
        x_min_diff = self.x_min - other.x_min
        if math.fmod(x_min_diff, self.cell_size) != 0.0:
            return False
        y_max_diff = self.y_max - other.y_max
        if math.fmod(y_max_diff, self.cell_size) != 0.0:
            return False
        return True

    def is_snapped_subset(self, other):
        """
        Tests whether self is a snapped subset of other
        """
        if not self.is_snapped(other):
            return False
        if not self.is_subset(other):
            return False
        return True

    def is_snapped_superset(self, other):
        """
        Tests whether self is a snapped superset of other
        """
        if not self.is_snapped(other):
            return False
        if not self.is_superset(other):
            return False
        return True

    def union(self, other, snap_this=True):
        """
        Union self and other and return a new RasterEnvelope instance.
        If snap_this is set to True, the returned envelope will align with
        self, otherwise it will align with other
        """
        if self.is_snapped_subset(other):
            return copy.copy(other)
        elif self.is_snapped_superset(other):
            return copy.copy(self)
        elif self.is_subset(other):
            if snap_this == True:
                return get_minimum_bounding_envelope(other, self)
            else:
                return copy.copy(other)
        elif self.is_superset(other):
            if snap_this == True:
                return copy.copy(self)
            else:
                return get_minimum_bounding_envelope(self, other)
        else:
            env = super(RasterEnvelope, self).union(other)
            if snap_this == True:
                return get_minimum_bounding_envelope(env, self)
            else:
                return get_minimum_bounding_envelope(env, other)

    def intersection(self, other, snap_this=True):
        """
        Intersect self and other and return a new RasterEnvelope instance.
        If snap_this is set to True, the returned envelope will align with
        self, otherwise it will align with other
        """
        if self.is_snapped_subset(other):
            return copy.copy(self)
        elif self.is_snapped_superset(other):
            return copy.copy(other)
        elif self.is_subset(other):
            if snap_this == True:
                return copy.copy(self)
            else:
                return get_minimum_bounding_envelope(self, other)
        elif self.is_superset(other):
            if snap_this == True:
                return get_minimum_bounding_envelope(other, self)
            else:
                return copy.copy(other)
        else:
            env = super(RasterEnvelope, self).intersection(other)
            if snap_this == True:
                return get_minimum_bounding_envelope(env, self)
            else:
                return get_minimum_bounding_envelope(env, other)

    def get_offset_from_xy(self, x, y):
        """
        Return the offset (ie. column and row) based on an x, y coordinate

        Parameters
        ----------
        x : double
            X coordinate

        y : double
            Y coordinate

        Returns
        -------
        (x_off, y_off) : tuple
            The X (column) and Y (row) offsets into the envelope
        """
        x_off = int(math.floor((x - self.x_min) / self.cell_size))
        y_off = int(math.floor((self.y_max - y) / self.cell_size))
        return (x_off, y_off)

    def get_xy_from_offset(self, x_off, y_off):
        """
        Return a cell's upper-left x, y coordinate based on a row/column offset

        Parameters
        ----------
        x_off : int
            X (column) offset

        y_off : int
            Y (row) offset

        Returns
        -------
        (x, y) : tuple
            The x, y coordinate of the upper-left corner on the offset cell
        """
        x = self.x_min + x_off * self.cell_size
        y = self.y_max - y_off * self.cell_size
        return (x, y)

    def get_geotransform(self):
        """
        Genereate a GDAL type geotransform based on this envelope properties
        """
        return [self.x_min, self.cell_size, 0.0, self.y_max, 0.0,
            -self.cell_size]


def get_num_cells(coord_max, coord_min, cell_size):
    """
    Given bounding coordinates and a cell size, determine the number of cells
    it takes to completely cover the range (in one dimension).  Because of
    floating-point approximations, calculations are done with decimal values

    Parameters
    ----------
    max : number (float, int, or decimal.Decimal)
        Maximum coordinate of the range

    min : number (float, int, or decimal.Decimal)
        Minimum coordinate of the range

    cell_size : number (float, int, or decimal.Decimal)
        Cellsize of the raster to cover the range

    Returns
    -------
    n_cells : int
        Number of cells to completely cover the range
    """

    # Convert range and cell_size to Decimal to ensure proper coordinate
    # precision when dividing
    coord_range = decimal.Decimal(str(coord_max - coord_min))
    cell_size = decimal.Decimal(str(cell_size))
    n_cells = int(coord_range / cell_size)

    # If there is any remainder, add another cell to completely cover the range
    if coord_range % cell_size:
        n_cells += 1
    return int(n_cells)


def calculate_snapped_window(env, cell_size):
    """
    Given an envelope and cell_size, ensure that the envelope is a
    multiple of cell_size.  Set the number of rows and columns and shift
    the lower right corner if necessary.

    Parameters
    ----------
    env : Envelope instance
        The envelope to snap

    cell_size : double
        The cell size to use for snapping

    Returns
    -------
    parameters : tuple
        Parameters for the snapped window as
        (x_max, y_min, x_size, y_size)
    """
    # Set rows and columns.  Adjust the number of rows and columns to be
    # a superset of the currently specified window if not a multiple of
    # cell_size (ie. 'grow' it from the upper left corner)
    x_size = get_num_cells(env.x_max, env.x_min, cell_size)
    y_size = get_num_cells(env.y_max, env.y_min, cell_size)

    # Adjust the lower right corner so that the envelope range is a
    # multiple of cell_size
    x_max = env.x_min + (x_size * cell_size)
    y_min = env.y_max - (y_size * cell_size)

    # Return these
    return (x_max, y_min, x_size, y_size)


def get_minimum_bounding_envelope(bound_env, snap_re):
    """
    Given a bounding envelope, bound_env return a new RasterEnvelope that
    minimally bounds while snapping to snap_re.

    Parameters
    ----------
    bound_env : Envelope
        The bounding envelope for which to get a new MBE

    snap_re : RasterEnvelope
        The envelope that provides the snap information

    Returns
    -------
    min_re : RasterEnvelope
        The minimum RasterEnvelop for which bound_env is a subset and that
        snaps to snap_env
    """

    # Discern the relationship between these two envelopes - if they are
    # disjoint, raise an exception
    if bound_env.is_disjoint(snap_re):
        err_str = 'The two envelopes do not overlap'
        raise EnvelopeError(err_str)

    # Get the starting row, column of the snap envelope for the
    # bound envelope
    (x_off, y_off) = \
        snap_re.get_offset_from_xy(bound_env.x_min, bound_env.y_max)

    # Adjust this envelope's upper left x,y coordinate to snap to a
    # pixel boundary
    x_min = snap_re.x_min + (x_off * snap_re.cell_size)
    y_max = snap_re.y_max - (y_off * snap_re.cell_size)

    # Create a raster envelope using the upper left coordinate
    min_re = RasterEnvelope(x_min, bound_env.y_min, bound_env.x_max, y_max,
        snap_re.cell_size)

    return min_re


def min_of(re_list, snap_re=None):
    """
    Given one or more RasterEnvelopes, return the RasterEnvelope that is the
    minimum bound.
    Parameters
    ----------
    re_list : sequence
        List or tuple of RasterEnvelope instances

    snap_re : RasterEnvelope
        The RasterEnvelope to use for the snapping environment

    Returns
    -------
    min_re : RasterEnvelope
        The minimum RasterEnvelop among all envelopes
    """

    if snap_re is None:
        snap_re = re_list[0]

    # Set the initial envelope to be that of the first passed envelope
    min_re = copy.deepcopy(re_list[0])
    for i in range(1, len(re_list)):
        min_env = min_re.intersection(re_list[i])
        min_re = get_minimum_bounding_envelope(min_env, snap_re)
    return min_re


def max_of(re_list, snap_re=None):
    """
    Given one or more RasterEnvelopes, return the RasterEnvelope that is the
    maximum bound.
    Parameters
    ----------
    re_list : sequence
        List or tuple of RasterEnvelope instances

    snap_re : RasterEnvelope
        The RasterEnvelope to use for the snapping environment

    Returns
    -------
    max_re : RasterEnvelope
        The maximum RasterEnvelop among all envelopes
    """

    if snap_re is None:
        snap_re = re_list[0]

    # Set the initial envelope to be that of the first passed envelope
    max_re = copy.deepcopy(re_list[0])
    for i in range(1, len(re_list)):
        max_env = max_re.union(re_list[i])
        max_re = get_minimum_bounding_envelope(max_env, snap_re)
    return max_re
