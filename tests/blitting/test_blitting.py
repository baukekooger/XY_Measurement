import matplotlib.pyplot as plt
import numpy as np
import time
import functools


def timed(func):
    @functools.wraps(func)
    def wrapper_timed(*args, **kwargs):
        tic = time.perf_counter()
        output = func(*args, **kwargs)
        toc = time.perf_counter()
        print(f'elapsed time: {toc-tic:.3f} seconds')
        return output
    return wrapper_timed


class BlitManager:
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
        if art.figure != self.canvas.figure:
            raise RuntimeError
        art.set_animated(True)
        self._artists.append(art)

    def _check_limits(self):
        """checks if the updated artist is within bounds of the current axes,
        adjusts axes if necessary, then redraws the canvas

        """

        data = self._artists[0]
        _, y = data.get_data()
        max_y_data = max(abs(y))
        min_ylim, max_ylim = data.axes.get_ylim()
        if max_y_data > max_ylim:
            data.axes.set_ylim(top=max_y_data*1.3)
            self.canvas.draw()

    def _draw_animated(self):
        """Draw all of the animated artists."""
        fig = self.canvas.figure
        for a in self._artists:
            fig.draw_artist(a)

    def update(self):
        """Update the screen with animated artists."""
        cv = self.canvas
        fig = cv.figure
        # paranoia in case we missed the draw event,
        if self._bg is None:
            self.on_draw(None)
        else:
            # restore the background
            cv.restore_region(self._bg)
            # draw all of the animated artists
            self._check_limits()
            self._draw_animated()
            # update the GUI state
            cv.blit(fig.bbox)
        # let the GUI event loop process anything it has to do
        cv.flush_events()


x = np.linspace(0, 2 * np.pi, 4000)


fig, ax = plt.subplots()
# add a line
(ln,) = ax.plot(x, 5*np.sin(x), animated=True)
# add a frame number
fr_number = ax.annotate(
    "0",
    (0, 1),
    xycoords="axes fraction",
    xytext=(10, -10),
    textcoords="offset points",
    ha="left",
    va="top",
    animated=True,
)
bm = BlitManager(fig.canvas, [ln, fr_number])
# make sure our window is on the screen and drawn
plt.show(block=False)
plt.pause(.1)


@timed
def do_animation_blit():
    for j in range(100):
        # min_y, max_y = ax.get_ylim()
        # maxabsy = max(list(map(abs, [min_y, max_y])))
        # update the artists
        ydata = 10*np.sin(j/100*np.pi)*np.sin(x)
        # if max(abs(ydata)) > 0.99 * maxabsy:
        #     print('data out of range')
        ln.set_ydata(ydata)
        fr_number.set_text("frame: {j}".format(j=j))
        # tell the blitting manager to do its thing
        bm.update()
        time.sleep(0.05)







