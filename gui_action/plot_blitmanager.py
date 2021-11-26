import logging


class BlitManager:
    """ Blitmanager class which enables easy blitting of all plots to speed
        up the plotting process, making the gui more responsive.

        There are various update methods included for different types of plots as different plots
        require different checks to check if data is still within axis limits.
    """
    def __init__(self, canvas, animated_artists=()):
        """
        Parameters
        ----------
        canvas : FigureCanvasAgg
            The canvas to work with, this only works for sub-classes of the Agg
            canvas which have the `~FigureCanvasAgg.copy_from_bbox` and
            `~FigureCanvasAgg.restore_region` methods.

        animated_artists : Iterable[Artist]
            List of the artists to manage
        """
        self.logger = logging.getLogger('plot.Blitmanager')
        self.logger.info(f'init blitmanager')
        self.canvas = canvas
        self._bg = None
        self._artists = []

        for a in animated_artists:
            self.add_artist(a)
        # grab the background on every draw
        self.cid = canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        """Callback to register with 'draw_event'."""

        cv = self.canvas
        if event is not None:
            if event.canvas != cv:
                raise RuntimeError
        self._bg = cv.copy_from_bbox(cv.figure.bbox)
        self._draw_animated()

    def add_artist(self, art):
        """
        Add an artist to be managed.

        Parameters
        ----------
        art : Artist

            The artist to be added.  Will be set to 'animated' (just
            to be safe).  *art* must be in the figure associated with
            the canvas this class is managing.

        """
        self.logger.debug(f'adding artist {art}')
        if art.figure != self.canvas.figure:
            raise RuntimeError
        art.set_animated(True)
        self._artists.append(art)

    def redraw_canvas_spectrometer(self):
        """ Redraw the canvas for the spectrometer to fit the axes """
        self.logger.info('redrawn canvas spectrometer')
        data = self._artists[0]
        _, y = data.get_data()
        max_y_data = max(y)
        min_y_data = min(y)
        spread_data = max_y_data-min_y_data
        data.axes.set_ylim(top=max_y_data + 0.1 * spread_data)
        data.axes.set_ylim(bottom=min_y_data - 0.1 * spread_data)

        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def redraw_canvas_digitizer(self):
        """ Redraw the canvas for the digitizer to fit the axes """
        self.logger.info('redrawn canvas digitizer')
        data = self._artists[0]
        times, values = data.get_data()
        max_values = max(values)
        min_values = min(values)
        spread_data = max_values - min_values

        data.axes.set_ylim(top=max_values + 0.1 * spread_data)
        data.axes.set_ylim(bottom=min_values - 0.1 * spread_data)
        data.axes.set_xlim(left=times[0], right=times[-1])

        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def redraw_canvas_powermeter(self):
        """ Redraw the canvas for the powermeter to fit the axes """
        self.logger.info('redrawn canvas powermeter')
        data = self._artists[0]
        _, y = data.get_data()
        max_y_data = max(y)
        min_y_data = min(y)
        spread_data = max_y_data - min_y_data
        data.axes.set_ylim(top=max_y_data + 0.1 * spread_data)
        data.axes.set_ylim(bottom=min_y_data - 0.1 * spread_data)

        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def _draw_animated(self):
        """Draw all of the animated artists."""
        self.logger.debug('drawing all artists')
        fig = self.canvas.figure
        for a in self._artists:
            fig.draw_artist(a)

    def update(self):
        """
        Update the screen with animated artists.
        """
        self.logger.debug('updating plots')
        cv = self.canvas
        fig = cv.figure
        # paranoia in case we missed the draw event,
        if self._bg is None:
            self.on_draw(None)
        else:
            # restore the background
            cv.restore_region(self._bg)
            # draw all of the animated artists
            self._draw_animated()
            # update the GUI state
            cv.blit(fig.bbox)
        # let the GUI event loop process anything it has to do
        cv.flush_events()


if __name__ == '__main__':
    # set up logging if file called directly
    from pathlib import Path
    import yaml
    import logging.config
    import logging.handlers
    pathlogging = Path(__file__).parent.parent / 'logging/loggingconfig_testing.yml'
    with pathlogging.open() as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)