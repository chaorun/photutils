# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This module defines background classes to estimate a scalar background
and background rms from an array (which may be masked) of any dimension.
These classes were designed as part of an object-oriented interface for
the tools in the PSF subpackage.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import abc
import numpy as np
from astropy.stats import (sigma_clip, mad_std, biweight_location,
                           biweight_midvariance)


__all__ = ['MeanBackground', 'MedianBackground', 'MMMBackground',
           'SExtractorBackground', 'BiweightLocationBackground',
           'StdBackgroundRMS', 'MADStdBackgroundRMS',
           'BiweightMidvarianceBackgroundRMS']

_bkgdoc = {}
_bkgdoc['sigclip_params'] = """sigma : float, optional
        The number of standard deviations to use for both the lower and
        upper clipping limit. These limits are overridden by
        ``sigma_lower`` and ``sigma_upper``, if input. Defaults to 3.
    sigma_lower : float or `None`, optional
        The number of standard deviations to use as the lower bound for
        the clipping limit. If `None` then the value of ``sigma`` is
        used. Defaults to `None`.
    sigma_upper : float or `None`, optional
        The number of standard deviations to use as the upper bound for
        the clipping limit. If `None` then the value of ``sigma`` is
        used. Defaults to `None`.
    iters : int or `None`, optional
        The number of iterations to perform sigma clipping, or `None` to
        clip until convergence is achieved (i.e., continue until the
        last iteration clips nothing). Defaults to 5.
"""


class BackgroundBase(object):
    """
    Base class for Background classes.

    Parameters
    ----------
    {sigclip_params}
    """

    def __init__(self, sigclip=True, sigma=3, sigma_lower=None,
                 sigma_upper=None, iters=5):

        self.sigclip = sigclip
        self.sigma = sigma
        self.sigma_lower = sigma_lower
        self.sigma_upper = sigma_upper
        self.iters = iters

    def sigma_clip(self, data):
        return sigma_clip(data, sigma=self.sigma,
                          sigma_lower=self.sigma_lower,
                          sigma_upper=self.sigma_upper,
                          iters=self.iters)

    @abc.abstractmethod
    def calc_background(self, data):
        """
        Calculate the background.

        Parameters
        ----------
        data : array_like or `~numpy.ma.MaskedArray`
            The array for which to calculate the background.

        Returns
        -------
        result : float
            The calculated background.
        """


BackgroundBase.__doc__ = BackgroundBase.__doc__.format(**_bkgdoc)


class MeanBackground(BackgroundBase):
    """
    Class to calculate the background in an array as the (sigma-clipped)
    mean.

    Parameters
    ----------
    {sigclip_params}
    """

    def __init__(self, **kwargs):

        super(MeanBackground, self).__init__(**kwargs)

    def calc_background(self, data):

        if self.sigclip:
            data = self.sigma_clip(data)
        return np.ma.mean(data)


MeanBackground.__doc__ = MeanBackground.__doc__.format(**_bkgdoc)


class MedianBackground(BackgroundBase):
    """
    Class to calculate the background in an array as the (sigma-clipped)
    median.

    Parameters
    ----------
    {sigclip_params}
    """

    def __init__(self, **kwargs):

        super(MedianBackground, self).__init__(**kwargs)

    def calc_background(self, data):

        if self.sigclip:
            data = self.sigma_clip(data)
        return np.ma.median(data)


MedianBackground.__doc__ = MedianBackground.__doc__.format(**_bkgdoc)


class MMMBackground(BackgroundBase):
    """
    Class to calculate the background in an array using the DAOPHOT MMM
    algorithm.

    The background is calculated using a mode estimator of the form
    ``(3 * median) - (2 * mean)``.

    Parameters
    ----------
    {sigclip_params}
    """

    def __init__(self, **kwargs):

        super(MMMBackground, self).__init__(**kwargs)

    def calc_background(self, data):

        if self.sigclip:
            data = self.sigma_clip(data)
        return (3. * np.ma.median(data)) - (2. * np.ma.mean(data))


MMMBackground.__doc__ = MMMBackground.__doc__.format(**_bkgdoc)


class SExtractorBackground(BackgroundBase):
    """
    Class to calculate the background in an array using the
    `SExtractor`_ algorithm.

    The background is calculated using a mode estimator of the form
    ``(2.5 * median) - (1.5 * mean)``.

    If ``(mean - median) / std > 0.3`` then the median is used instead.
    Despite what the `SExtractor`_ User's Manual says, this is the
    method it *always* uses.

    .. _SExtractor: http://www.astromatic.net/software/sextractor

    Parameters
    ----------
    {sigclip_params}
    """

    def __init__(self, **kwargs):

        super(SExtractorBackground, self).__init__(**kwargs)

    def calc_background(self, data):

        if self.sigclip:
            data = self.sigma_clip(data)
        _median = np.ma.median(data)
        _mean = np.ma.mean(data)
        _std = np.ma.std(data)

        if _std == 0:
            return _mean

        if (np.abs(_mean - _median) / _std) < 0.3:
            return (2.5 * _median) - (1.5 * _mean)
        else:
            return _median


SExtractorBackground.__doc__ = SExtractorBackground.__doc__.format(**_bkgdoc)


class BiweightLocationBackground(BackgroundBase):
    """
    Class to calculate the background in an array using the biweight
    location.

    Parameters
    ----------
    c : float, optional
        Tuning constant for the biweight estimator.  Default value is
        6.0.
    M : float, optional
        Initial guess for the biweight location.  Default value is
        `None`.
    {sigclip_params}
    """

    def __init__(self, c=6, M=None, **kwargs):

        super(BiweightLocationBackground, self).__init__(**kwargs)
        self.c = c
        self.M = M

    def calc_background(self, data):

        if self.sigclip:
            data = self.sigma_clip(data)
        return biweight_location(data, c=self.c, M=self.M)


BiweightLocationBackground.__doc__ = (
    BiweightLocationBackground.__doc__.format(**_bkgdoc))


class StdBackgroundRMS(BackgroundBase):
    """
    Class to calculate the background rms in an array as the
    (sigma-clipped) standard deviation.

    Parameters
    ----------
    {sigclip_params}
    """

    def __init__(self, **kwargs):

        super(StdBackgroundRMS, self).__init__(**kwargs)

    def calc_background_rms(self, data):

        if self.sigclip:
            data = self.sigma_clip(data)
        return np.ma.std(data)


StdBackgroundRMS.__doc__ = StdBackgroundRMS.__doc__.format(**_bkgdoc)


class MADStdBackgroundRMS(BackgroundBase):
    """
    Class to calculate the background rms in an array as using the
    `median absolute deviation (MAD)
    <http://en.wikipedia.org/wiki/Median_absolute_deviation>`_.

    The standard deviation estimator is given by:

    .. math::

        \\sigma \\approx \\frac{{\\textrm{{MAD}}}}{{\Phi^{{-1}}(3/4)}}
            \\approx 1.4826 \ \\textrm{{MAD}}

    where :math:`\Phi^{{-1}}(P)` is the normal inverse cumulative
    distribution function evaluated at probability :math:`P = 3/4`.

    Parameters
    ----------
    {sigclip_params}
    """

    def __init__(self, **kwargs):

        super(MADStdBackgroundRMS, self).__init__(**kwargs)

    def calc_background_rms(self, data):

        if self.sigclip:
            data = self.sigma_clip(data)
        return mad_std(data)


MADStdBackgroundRMS.__doc__ = MADStdBackgroundRMS.__doc__.format(**_bkgdoc)


class BiweightMidvarianceBackgroundRMS(BackgroundBase):
    """
    Class to calculate the background rms in an array as the
    (sigma-clipped) biweight midvariance.

    Parameters
    ----------
    c : float, optional
        Tuning constant for the biweight estimator.  Default value is
        9.0.
    M : float, optional
        Initial guess for the biweight location.  Default value is
        `None`.
    {sigclip_params}
    """

    def __init__(self, c=9.0, M=None, **kwargs):

        super(BiweightMidvarianceBackgroundRMS, self).__init__(**kwargs)
        self.c = c
        self.M = M

    def calc_background_rms(self, data):

        if self.sigclip:
            data = self.sigma_clip(data)
        return biweight_midvariance(data, c=self.c, M=self.M)


BiweightMidvarianceBackgroundRMS.__doc__ = (
    BiweightMidvarianceBackgroundRMS.__doc__.format(**_bkgdoc))
