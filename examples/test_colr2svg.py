import cairosvg
from colr_to_svg import Colr2SVG
from matplotlib.offsetbox import AnnotationBbox

from mpl_simple_svg_parser import SVGMplPathIterator
from mpl_simple_svg_parser.svg_helper import get_svg_drawing_area


if True:
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    import io

    # ftname = 'Noto-COLRv1-emojicompat.ttf'
    ftname = 'Noto-COLRv1.ttf'
    # ftname = "Twemoji.Mozilla.ttf"
    # ftname = 'ions.woff2'

    ch = Colr2SVG(ftname)

    # c = "🤐"
    # c = '🇰🇷'
    # c = "😱"
    # c = "🤩"
    # c = "👽"
    # c = "🍵"
    # c = '☕'
    c = "😂"

    svg_el = ch.get(c)

    b_xmlstring = Colr2SVG.tostring(Colr2SVG.get_scaled_svg(svg_el, 128))
    png = cairosvg.svg2png(b_xmlstring) # , parent_width=w, parent_height=h-d)
    arr = mpimg.imread(io.BytesIO(png))

    fig, axs = plt.subplots(1, 2, figsize=(10, 5), clear=True, num=1)

    axs[0].imshow(arr)

    # draw as a path

    ax = axs[1]

    svg_mpl_path_iterator = SVGMplPathIterator(b_xmlstring, svg2svg=True)

    da = get_svg_drawing_area(ax, svg_mpl_path_iterator)
    ann = AnnotationBbox(da, (0.5, 0.5), frameon=False)
    ax.add_artist(ann)

    plt.show()
