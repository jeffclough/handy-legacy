# Table of Contents

* [png](#png)
  * [adam7\_generate](#png.adam7_generate)
  * [check\_palette](#png.check_palette)
  * [check\_sizes](#png.check_sizes)
  * [check\_color](#png.check_color)
  * [FormatError](#png.FormatError)
  * [ProtocolError](#png.ProtocolError)
  * [Default](#png.Default)
  * [Writer](#png.Writer)
    * [\_\_init\_\_](#png.Writer.__init__)
    * [write](#png.Writer.write)
    * [write\_passes](#png.Writer.write_passes)
    * [write\_packed](#png.Writer.write_packed)
    * [write\_array](#png.Writer.write_array)
    * [array\_scanlines](#png.Writer.array_scanlines)
    * [array\_scanlines\_interlace](#png.Writer.array_scanlines_interlace)
  * [write\_chunk](#png.write_chunk)
  * [write\_chunks](#png.write_chunks)
  * [rescale\_rows](#png.rescale_rows)
  * [pack\_rows](#png.pack_rows)
  * [unpack\_rows](#png.unpack_rows)
  * [make\_palette\_chunks](#png.make_palette_chunks)
  * [check\_bitdepth\_rescale](#png.check_bitdepth_rescale)
  * [from\_array](#png.from_array)
  * [Image](#png.Image)
    * [\_\_init\_\_](#png.Image.__init__)
    * [save](#png.Image.save)
    * [write](#png.Image.write)
  * [Reader](#png.Reader)
    * [\_\_init\_\_](#png.Reader.__init__)
    * [chunk](#png.Reader.chunk)
    * [chunks](#png.Reader.chunks)
    * [undo\_filter](#png.Reader.undo_filter)
    * [validate\_signature](#png.Reader.validate_signature)
    * [preamble](#png.Reader.preamble)
    * [process\_chunk](#png.Reader.process_chunk)
    * [read](#png.Reader.read)
    * [read\_flat](#png.Reader.read_flat)
    * [palette](#png.Reader.palette)
    * [asDirect](#png.Reader.asDirect)
    * [asRGB8](#png.Reader.asRGB8)
    * [asRGBA8](#png.Reader.asRGBA8)
    * [asRGB](#png.Reader.asRGB)
    * [asRGBA](#png.Reader.asRGBA)
  * [decompress](#png.decompress)
  * [check\_bitdepth\_colortype](#png.check_bitdepth_colortype)
  * [is\_natural](#png.is_natural)
  * [undo\_filter\_sub](#png.undo_filter_sub)
  * [undo\_filter\_up](#png.undo_filter_up)
  * [undo\_filter\_average](#png.undo_filter_average)
  * [undo\_filter\_paeth](#png.undo_filter_paeth)
  * [convert\_l\_to\_rgba](#png.convert_l_to_rgba)
  * [convert\_rgb\_to\_rgba](#png.convert_rgb_to_rgba)
  * [binary\_stdin](#png.binary_stdin)
  * [binary\_stdout](#png.binary_stdout)
  * [main](#png.main)

<a name="png"></a>
# png

The ``png`` module can read and write PNG files.

Installation and Overview
-------------------------

``pip install pypng``

For help, type ``import png; help(png)`` in your python interpreter.

A good place to start is the :class:`Reader` and :class:`Writer` classes.

Coverage of PNG formats is fairly complete;
all allowable bit depths (1/2/4/8/16/24/32/48/64 bits per pixel) and
colour combinations are supported:

- greyscale (1/2/4/8/16 bit);
- RGB, RGBA, LA (greyscale with alpha) with 8/16 bits per channel;
- colour mapped images (1/2/4/8 bit).

Interlaced images,
which support a progressive display when downloading,
are supported for both reading and writing.

A number of optional chunks can be specified (when writing)
and understood (when reading): ``tRNS``, ``bKGD``, ``gAMA``.

The ``sBIT`` chunk can be used to specify precision for
non-native bit depths.

Requires Python 3.4 or higher.
Installation is trivial,
but see the ``README.txt`` file (with the source distribution) for details.

Full use of all features will need some reading of the PNG specification
http://www.w3.org/TR/2003/REC-PNG-20031110/.

The package also comes with command line utilities.

- ``pripamtopng`` converts
  `Netpbm <http://netpbm.sourceforge.net/>`_ PAM/PNM files to PNG;
- ``pripngtopam`` converts PNG to file PAM/PNM.

There are a few more for simple PNG manipulations.

Spelling and Terminology
------------------------

Generally British English spelling is used in the documentation.
So that's "greyscale" and "colour".
This not only matches the author's native language,
it's also used by the PNG specification.

Colour Models
-------------

The major colour models supported by PNG (and hence by PyPNG) are:

- greyscale;
- greyscale--alpha;
- RGB;
- RGB--alpha.

Also referred to using the abbreviations: L, LA, RGB, RGBA.
Each letter codes a single channel:
*L* is for Luminance or Luma or Lightness (greyscale images);
*A* stands for Alpha, the opacity channel
(used for transparency effects, but higher values are more opaque,
so it makes sense to call it opacity);
*R*, *G*, *B* stand for Red, Green, Blue (colour image).

Lists, arrays, sequences, and so on
-----------------------------------

When getting pixel data out of this module (reading) and
presenting data to this module (writing) there are
a number of ways the data could be represented as a Python value.

The preferred format is a sequence of *rows*,
which each row being a sequence of *values*.
In this format, the values are in pixel order,
with all the values from all the pixels in a row
being concatenated into a single sequence for that row.

Consider an image that is 3 pixels wide by 2 pixels high, and each pixel
has RGB components:

Sequence of rows::

  list([R,G,B, R,G,B, R,G,B],
       [R,G,B, R,G,B, R,G,B])

Each row appears as its own list,
but the pixels are flattened so that three values for one pixel
simply follow the three values for the previous pixel.

This is the preferred because
it provides a good compromise between space and convenience.
PyPNG regards itself as at liberty to replace any sequence type with
any sufficiently compatible other sequence type;
in practice each row is an array (``bytearray`` or ``array.array``).

To allow streaming the outer list is sometimes
an iterator rather than an explicit list.

An alternative format is a single array holding all the values.

Array of values::

  [R,G,B, R,G,B, R,G,B,
   R,G,B, R,G,B, R,G,B]

The entire image is one single giant sequence of colour values.
Generally an array will be used (to save space), not a list.

The top row comes first,
and within each row the pixels are ordered from left-to-right.
Within a pixel the values appear in the order R-G-B-A
(or L-A for greyscale--alpha).

There is another format, which should only be used with caution.
It is mentioned because it is used internally,
is close to what lies inside a PNG file itself,
and has some support from the public API.
This format is called *packed*.
When packed, each row is a sequence of bytes (integers from 0 to 255),
just as it is before PNG scanline filtering is applied.
When the bit depth is 8 this is the same as a sequence of rows;
when the bit depth is less than 8 (1, 2 and 4),
several pixels are packed into each byte;
when the bit depth is 16 each pixel value is decomposed into 2 bytes
(and `packed` is a misnomer).
This format is used by the :meth:`Writer.write_packed` method.
It isn't usually a convenient format,
but may be just right if the source data for
the PNG image comes from something that uses a similar format
(for example, 1-bit BMPs, or another PNG file).

<a name="png.adam7_generate"></a>
#### adam7\_generate

```python
adam7_generate(width, height)
```

Generate the coordinates for the reduced scanlines
of an Adam7 interlaced image
of size `width` by `height` pixels.

Yields a generator for each pass,
and each pass generator yields a series of (x, y, xstep) triples,
each one identifying a reduced scanline consisting of
pixels starting at (x, y) and taking every xstep pixel to the right.

<a name="png.check_palette"></a>
#### check\_palette

```python
check_palette(palette)
```

Check a palette argument (to the :class:`Writer` class) for validity.
Returns the palette as a list if okay;
raises an exception otherwise.

<a name="png.check_sizes"></a>
#### check\_sizes

```python
check_sizes(size, width, height)
```

Check that these arguments, if supplied, are consistent.
Return a (width, height) pair.

<a name="png.check_color"></a>
#### check\_color

```python
check_color(c, greyscale, which)
```

Checks that a colour argument for transparent or background options
is the right form.
Returns the colour
(which, if it's a bare integer, is "corrected" to a 1-tuple).

<a name="png.FormatError"></a>
## FormatError Objects

```python
class FormatError(Error)
```

Problem with input file format.
In other words, PNG file does not conform to
the specification in some way and is invalid.

<a name="png.ProtocolError"></a>
## ProtocolError Objects

```python
class ProtocolError(Error)
```

Problem with the way the programming interface has been used,
or the data presented to it.

<a name="png.Default"></a>
## Default Objects

```python
class Default()
```

The default for the greyscale paramter.

<a name="png.Writer"></a>
## Writer Objects

```python
class Writer()
```

PNG encoder in pure Python.

<a name="png.Writer.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(width=None, height=None, size=None, greyscale=Default, alpha=False, bitdepth=8, palette=None, transparent=None, background=None, gamma=None, compression=None, interlace=False, planes=None, colormap=None, maxval=None, chunk_limit=2**20, x_pixels_per_unit=None, y_pixels_per_unit=None, unit_is_meter=False)
```

Create a PNG encoder object.

**Arguments**:

  
  width, height
  Image size in pixels, as two separate arguments.
  size
  Image size (w,h) in pixels, as single argument.
  greyscale
  Pixels are greyscale, not RGB.
  alpha
  Input data has alpha channel (RGBA or LA).
  bitdepth
  Bit depth: from 1 to 16 (for each channel).
  palette
  Create a palette for a colour mapped image (colour type 3).
  transparent
  Specify a transparent colour (create a ``tRNS`` chunk).
  background
  Specify a default background colour (create a ``bKGD`` chunk).
  gamma
  Specify a gamma value (create a ``gAMA`` chunk).
  compression
  zlib compression level: 0 (none) to 9 (more compressed);
- `default` - -1 or None.
  interlace
  Create an interlaced image.
  chunk_limit
  Write multiple ``IDAT`` chunks to save memory.
  x_pixels_per_unit
  Number of pixels a unit along the x axis (write a
  `pHYs` chunk).
  y_pixels_per_unit
  Number of pixels a unit along the y axis (write a
  `pHYs` chunk). Along with `x_pixel_unit`, this gives
  the pixel size ratio.
  unit_is_meter
  `True` to indicate that the unit (for the `pHYs`
  chunk) is metre.
  
  The image size (in pixels) can be specified either by using the
  `width` and `height` arguments, or with the single `size`
  argument.
  If `size` is used it should be a pair (*width*, *height*).
  
  The `greyscale` argument indicates whether input pixels
  are greyscale (when true), or colour (when false).
  The default is true unless `palette=` is used.
  
  The `alpha` argument (a boolean) specifies
  whether input pixels have an alpha channel (or not).
  
  `bitdepth` specifies the bit depth of the source pixel values.
  Each channel may have a different bit depth.
  Each source pixel must have values that are
  an integer between 0 and ``2**bitdepth-1``, where
  `bitdepth` is the bit depth for the corresponding channel.
  For example, 8-bit images have values between 0 and 255.
  PNG only stores images with bit depths of
  1,2,4,8, or 16 (the same for all channels).
  When `bitdepth` is not one of these values or where
  channels have different bit depths,
  the next highest valid bit depth is selected,
  and an ``sBIT`` (significant bits) chunk is generated
  that specifies the original precision of the source image.
  In this case the supplied pixel values will be rescaled to
  fit the range of the selected bit depth.
  
  The PNG file format supports many bit depth / colour model
  combinations, but not all.
  The details are somewhat arcane
  (refer to the PNG specification for full details).
  Briefly:
  Bit depths < 8 (1,2,4) are only allowed with greyscale and
  colour mapped images;
  colour mapped images cannot have bit depth 16.
  
  For colour mapped images
  (in other words, when the `palette` argument is specified)
  the `bitdepth` argument must match one of
  the valid PNG bit depths: 1, 2, 4, or 8.
  (It is valid to have a PNG image with a palette and
  an ``sBIT`` chunk, but the meaning is slightly different;
  it would be awkward to use the `bitdepth` argument for this.)
  
  The `palette` option, when specified,
  causes a colour mapped image to be created:
  the PNG colour type is set to 3;
  `greyscale` must not be true; `alpha` must not be true;
  `transparent` must not be set.
  The bit depth must be 1,2,4, or 8.
  When a colour mapped image is created,
  the pixel values are palette indexes and
  the `bitdepth` argument specifies the size of these indexes
  (not the size of the colour values in the palette).
  
  The palette argument value should be a sequence of 3- or
  4-tuples.
  3-tuples specify RGB palette entries;
  4-tuples specify RGBA palette entries.
  All the 4-tuples (if present) must come before all the 3-tuples.
  A ``PLTE`` chunk is created;
  if there are 4-tuples then a ``tRNS`` chunk is created as well.
  The ``PLTE`` chunk will contain all the RGB triples in the same
  sequence;
  the ``tRNS`` chunk will contain the alpha channel for
  all the 4-tuples, in the same sequence.
  Palette entries are always 8-bit.
  
  If specified, the `transparent` and `background` parameters must be
  a tuple with one element for each channel in the image.
  Either a 3-tuple of integer (RGB) values for a colour image, or
  a 1-tuple of a single integer for a greyscale image.
  
  If specified, the `gamma` parameter must be a positive number
  (generally, a `float`).
  A ``gAMA`` chunk will be created.
  Note that this will not change the values of the pixels as
  they appear in the PNG file,
  they are assumed to have already
  been converted appropriately for the gamma specified.
  
  The `compression` argument specifies the compression level to
  be used by the ``zlib`` module.
  Values from 1 to 9 (highest) specify compression.
  0 means no compression.
  -1 and ``None`` both mean that the ``zlib`` module uses
  the default level of compession (which is generally acceptable).
  
  If `interlace` is true then an interlaced image is created
  (using PNG's so far only interace method, *Adam7*).
  This does not affect how the pixels should be passed in,
  rather it changes how they are arranged into the PNG file.
  On slow connexions interlaced images can be
  partially decoded by the browser to give
  a rough view of the image that is
  successively refined as more image data appears.
  
  .. note ::
  
  Enabling the `interlace` option requires the entire image
  to be processed in working memory.
  
  `chunk_limit` is used to limit the amount of memory used whilst
  compressing the image.
  In order to avoid using large amounts of memory,
  multiple ``IDAT`` chunks may be created.

<a name="png.Writer.write"></a>
#### write

```python
 | write(outfile, rows)
```

Write a PNG image to the output file.
`rows` should be an iterable that yields each row
(each row is a sequence of values).
The rows should be the rows of the original image,
so there should be ``self.height`` rows of
``self.width * self.planes`` values.
If `interlace` is specified (when creating the instance),
then an interlaced PNG file will be written.
Supply the rows in the normal image order;
the interlacing is carried out internally.

.. note ::

  Interlacing requires the entire image to be in working memory.

<a name="png.Writer.write_passes"></a>
#### write\_passes

```python
 | write_passes(outfile, rows)
```

Write a PNG image to the output file.

Most users are expected to find the :meth:`write` or
:meth:`write_array` method more convenient.

The rows should be given to this method in the order that
they appear in the output file.
For straightlaced images, this is the usual top to bottom ordering.
For interlaced images the rows should have been interlaced before
passing them to this function.

`rows` should be an iterable that yields each row
(each row being a sequence of values).

<a name="png.Writer.write_packed"></a>
#### write\_packed

```python
 | write_packed(outfile, rows)
```

Write PNG file to `outfile`.
`rows` should be an iterator that yields each packed row;
a packed row being a sequence of packed bytes.

The rows have a filter byte prefixed and
are then compressed into one or more IDAT chunks.
They are not processed any further,
so if bitdepth is other than 1, 2, 4, 8, 16,
the pixel values should have been scaled
before passing them to this method.

This method does work for interlaced images but it is best avoided.
For interlaced images, the rows should be
presented in the order that they appear in the file.

<a name="png.Writer.write_array"></a>
#### write\_array

```python
 | write_array(outfile, pixels)
```

Write an array that holds all the image values
as a PNG file on the output file.
See also :meth:`write` method.

<a name="png.Writer.array_scanlines"></a>
#### array\_scanlines

```python
 | array_scanlines(pixels)
```

Generates rows (each a sequence of values) from
a single array of values.

<a name="png.Writer.array_scanlines_interlace"></a>
#### array\_scanlines\_interlace

```python
 | array_scanlines_interlace(pixels)
```

Generator for interlaced scanlines from an array.
`pixels` is the full source image as a single array of values.
The generator yields each scanline of the reduced passes in turn,
each scanline being a sequence of values.

<a name="png.write_chunk"></a>
#### write\_chunk

```python
write_chunk(outfile, tag, data=b'')
```

Write a PNG chunk to the output file, including length and
checksum.

<a name="png.write_chunks"></a>
#### write\_chunks

```python
write_chunks(out, chunks)
```

Create a PNG file by writing out the chunks.

<a name="png.rescale_rows"></a>
#### rescale\_rows

```python
rescale_rows(rows, rescale)
```

Take each row in rows (an iterator) and yield
a fresh row with the pixels scaled according to
the rescale parameters in the list `rescale`.
Each element of `rescale` is a tuple of
(source_bitdepth, target_bitdepth),
with one element per channel.

<a name="png.pack_rows"></a>
#### pack\_rows

```python
pack_rows(rows, bitdepth)
```

Yield packed rows that are a byte array.
Each byte is packed with the values from several pixels.

<a name="png.unpack_rows"></a>
#### unpack\_rows

```python
unpack_rows(rows)
```

Unpack each row from being 16-bits per value,
to being a sequence of bytes.

<a name="png.make_palette_chunks"></a>
#### make\_palette\_chunks

```python
make_palette_chunks(palette)
```

Create the byte sequences for a ``PLTE`` and
if necessary a ``tRNS`` chunk.
Returned as a pair (*p*, *t*).
*t* will be ``None`` if no ``tRNS`` chunk is necessary.

<a name="png.check_bitdepth_rescale"></a>
#### check\_bitdepth\_rescale

```python
check_bitdepth_rescale(palette, bitdepth, transparent, alpha, greyscale)
```

Returns (bitdepth, rescale) pair.

<a name="png.from_array"></a>
#### from\_array

```python
from_array(a, mode=None, info={})
```

Create a PNG :class:`Image` object from a 2-dimensional array.
One application of this function is easy PIL-style saving:
``png.from_array(pixels, 'L').save('foo.png')``.

Unless they are specified using the *info* parameter,
the PNG's height and width are taken from the array size.
The first axis is the height; the second axis is the
ravelled width and channel index.
The array is treated is a sequence of rows,
each row being a sequence of values (``width*channels`` in number).
So an RGB image that is 16 pixels high and 8 wide will
occupy a 2-dimensional array that is 16x24
(each row will be 8*3 = 24 sample values).

*mode* is a string that specifies the image colour format in a
PIL-style mode.  It can be:

``'L'``
  greyscale (1 channel)
``'LA'``
  greyscale with alpha (2 channel)
``'RGB'``
  colour image (3 channel)
``'RGBA'``
  colour image with alpha (4 channel)

The mode string can also specify the bit depth
(overriding how this function normally derives the bit depth,
see below).
Appending ``';16'`` to the mode will cause the PNG to be
16 bits per channel;
any decimal from 1 to 16 can be used to specify the bit depth.

When a 2-dimensional array is used *mode* determines how many
channels the image has, and so allows the width to be derived from
the second array dimension.

The array is expected to be a ``numpy`` array,
but it can be any suitable Python sequence.
For example, a list of lists can be used:
``png.from_array([[0, 255, 0], [255, 0, 255]], 'L')``.
The exact rules are: ``len(a)`` gives the first dimension, height;
``len(a[0])`` gives the second dimension.
It's slightly more complicated than that because
an iterator of rows can be used, and it all still works.
Using an iterator allows data to be streamed efficiently.

The bit depth of the PNG is normally taken from
the array element's datatype
(but if *mode* specifies a bitdepth then that is used instead).
The array element's datatype is determined in a way which
is supposed to work both for ``numpy`` arrays and for Python
``array.array`` objects.
A 1 byte datatype will give a bit depth of 8,
a 2 byte datatype will give a bit depth of 16.
If the datatype does not have an implicit size,
like the above example where it is a plain Python list of lists,
then a default of 8 is used.

The *info* parameter is a dictionary that can
be used to specify metadata (in the same style as
the arguments to the :class:`png.Writer` class).
For this function the keys that are useful are:

height
  overrides the height derived from the array dimensions and
  allows *a* to be an iterable.
width
  overrides the width derived from the array dimensions.
bitdepth
  overrides the bit depth derived from the element datatype
  (but must match *mode* if that also specifies a bit depth).

Generally anything specified in the *info* dictionary will
override any implicit choices that this function would otherwise make,
but must match any explicit ones.
For example, if the *info* dictionary has a ``greyscale`` key then
this must be true when mode is ``'L'`` or ``'LA'`` and
false when mode is ``'RGB'`` or ``'RGBA'``.

<a name="png.Image"></a>
## Image Objects

```python
class Image()
```

A PNG image.  You can create an :class:`Image` object from
an array of pixels by calling :meth:`png.from_array`.  It can be
saved to disk with the :meth:`save` method.

<a name="png.Image.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(rows, info)
```

.. note ::

  The constructor is not public.  Please do not call it.

<a name="png.Image.save"></a>
#### save

```python
 | save(file)
```

Save the image to the named *file*.

See `.write()` if you already have an open file object.

In general, you can only call this method once;
after it has been called the first time the PNG image is written,
the source data will have been streamed, and
cannot be streamed again.

<a name="png.Image.write"></a>
#### write

```python
 | write(file)
```

Write the image to the open file object.

See `.save()` if you have a filename.

In general, you can only call this method once;
after it has been called the first time the PNG image is written,
the source data will have been streamed, and
cannot be streamed again.

<a name="png.Reader"></a>
## Reader Objects

```python
class Reader()
```

Pure Python PNG decoder in pure Python.

<a name="png.Reader.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(_guess=None, filename=None, file=None, bytes=None)
```

The constructor expects exactly one keyword argument.
If you supply a positional argument instead,
it will guess the input type.
Choose from the following keyword arguments:

filename
  Name of input file (a PNG file).
file
  A file-like object (object with a read() method).
bytes
  ``bytes`` or ``bytearray`` with PNG data.

<a name="png.Reader.chunk"></a>
#### chunk

```python
 | chunk(lenient=False)
```

Read the next PNG chunk from the input file;
returns a (*type*, *data*) tuple.
*type* is the chunk's type as a byte string
(all PNG chunk types are 4 bytes long).
*data* is the chunk's data content, as a byte string.

If the optional `lenient` argument evaluates to `True`,
checksum failures will raise warnings rather than exceptions.

<a name="png.Reader.chunks"></a>
#### chunks

```python
 | chunks()
```

Return an iterator that will yield each chunk as a
(*chunktype*, *content*) pair.

<a name="png.Reader.undo_filter"></a>
#### undo\_filter

```python
 | undo_filter(filter_type, scanline, previous)
```

Undo the filter for a scanline.
`scanline` is a sequence of bytes that
does not include the initial filter type byte.
`previous` is decoded previous scanline
(for straightlaced images this is the previous pixel row,
but for interlaced images, it is
the previous scanline in the reduced image,
which in general is not the previous pixel row in the final image).
When there is no previous scanline
(the first row of a straightlaced image,
or the first row in one of the passes in an interlaced image),
then this argument should be ``None``.

The scanline will have the effects of filtering removed;
the result will be returned as a fresh sequence of bytes.

<a name="png.Reader.validate_signature"></a>
#### validate\_signature

```python
 | validate_signature()
```

If signature (header) has not been read then read and
validate it; otherwise do nothing.

<a name="png.Reader.preamble"></a>
#### preamble

```python
 | preamble(lenient=False)
```

Extract the image metadata by reading
the initial part of the PNG file up to
the start of the ``IDAT`` chunk.
All the chunks that precede the ``IDAT`` chunk are
read and either processed for metadata or discarded.

If the optional `lenient` argument evaluates to `True`,
checksum failures will raise warnings rather than exceptions.

<a name="png.Reader.process_chunk"></a>
#### process\_chunk

```python
 | process_chunk(lenient=False)
```

Process the next chunk and its data.
This only processes the following chunk types:
``IHDR``, ``PLTE``, ``bKGD``, ``tRNS``, ``gAMA``, ``sBIT``, ``pHYs``.
All other chunk types are ignored.

If the optional `lenient` argument evaluates to `True`,
checksum failures will raise warnings rather than exceptions.

<a name="png.Reader.read"></a>
#### read

```python
 | read(lenient=False)
```

Read the PNG file and decode it.
Returns (`width`, `height`, `rows`, `info`).

May use excessive memory.

`rows` is a sequence of rows;
each row is a sequence of values.

If the optional `lenient` argument evaluates to True,
checksum failures will raise warnings rather than exceptions.

<a name="png.Reader.read_flat"></a>
#### read\_flat

```python
 | read_flat()
```

Read a PNG file and decode it into a single array of values.
Returns (*width*, *height*, *values*, *info*).

May use excessive memory.

`values` is a single array.

The :meth:`read` method is more stream-friendly than this,
because it returns a sequence of rows.

<a name="png.Reader.palette"></a>
#### palette

```python
 | palette(alpha='natural')
```

Returns a palette that is a sequence of 3-tuples or 4-tuples,
synthesizing it from the ``PLTE`` and ``tRNS`` chunks.
These chunks should have already been processed (for example,
by calling the :meth:`preamble` method).
All the tuples are the same size:
3-tuples if there is no ``tRNS`` chunk,
4-tuples when there is a ``tRNS`` chunk.

Assumes that the image is colour type
3 and therefore a ``PLTE`` chunk is required.

If the `alpha` argument is ``'force'`` then an alpha channel is
always added, forcing the result to be a sequence of 4-tuples.

<a name="png.Reader.asDirect"></a>
#### asDirect

```python
 | asDirect()
```

Returns the image data as a direct representation of
an ``x * y * planes`` array.
This removes the need for callers to deal with
palettes and transparency themselves.
Images with a palette (colour type 3) are converted to RGB or RGBA;
images with transparency (a ``tRNS`` chunk) are converted to
LA or RGBA as appropriate.
When returned in this format the pixel values represent
the colour value directly without needing to refer
to palettes or transparency information.

Like the :meth:`read` method this method returns a 4-tuple:

(*width*, *height*, *rows*, *info*)

This method normally returns pixel values with
the bit depth they have in the source image, but
when the source PNG has an ``sBIT`` chunk it is inspected and
can reduce the bit depth of the result pixels;
pixel values will be reduced according to the bit depth
specified in the ``sBIT`` chunk.
PNG nerds should note a single result bit depth is
used for all channels:
the maximum of the ones specified in the ``sBIT`` chunk.
An RGB565 image will be rescaled to 6-bit RGB666.

The *info* dictionary that is returned reflects
the `direct` format and not the original source image.
For example, an RGB source image with a ``tRNS`` chunk
to represent a transparent colour,
will start with ``planes=3`` and ``alpha=False`` for the
source image,
but the *info* dictionary returned by this method
will have ``planes=4`` and ``alpha=True`` because
an alpha channel is synthesized and added.

*rows* is a sequence of rows;
each row being a sequence of values
(like the :meth:`read` method).

All the other aspects of the image data are not changed.

<a name="png.Reader.asRGB8"></a>
#### asRGB8

```python
 | asRGB8()
```

Return the image data as an RGB pixels with 8-bits per sample.
This is like the :meth:`asRGB` method except that
this method additionally rescales the values so that
they are all between 0 and 255 (8-bit).
In the case where the source image has a bit depth < 8
the transformation preserves all the information;
where the source image has bit depth > 8, then
rescaling to 8-bit values loses precision.
No dithering is performed.
Like :meth:`asRGB`,
an alpha channel in the source image will raise an exception.

This function returns a 4-tuple:
(*width*, *height*, *rows*, *info*).
*width*, *height*, *info* are as per the :meth:`read` method.

*rows* is the pixel data as a sequence of rows.

<a name="png.Reader.asRGBA8"></a>
#### asRGBA8

```python
 | asRGBA8()
```

Return the image data as RGBA pixels with 8-bits per sample.
This method is similar to :meth:`asRGB8` and :meth:`asRGBA`:
The result pixels have an alpha channel, *and*
values are rescaled to the range 0 to 255.
The alpha channel is synthesized if necessary
(with a small speed penalty).

<a name="png.Reader.asRGB"></a>
#### asRGB

```python
 | asRGB()
```

Return image as RGB pixels.
RGB colour images are passed through unchanged;
greyscales are expanded into RGB triplets
(there is a small speed overhead for doing this).

An alpha channel in the source image will raise an exception.

The return values are as for the :meth:`read` method except that
the *info* reflect the returned pixels, not the source image.
In particular,
for this method ``info['greyscale']`` will be ``False``.

<a name="png.Reader.asRGBA"></a>
#### asRGBA

```python
 | asRGBA()
```

Return image as RGBA pixels.
Greyscales are expanded into RGB triplets;
an alpha channel is synthesized if necessary.
The return values are as for the :meth:`read` method except that
the *info* reflect the returned pixels, not the source image.
In particular, for this method
``info['greyscale']`` will be ``False``, and
``info['alpha']`` will be ``True``.

<a name="png.decompress"></a>
#### decompress

```python
decompress(data_blocks)
```

`data_blocks` should be an iterable that
yields the compressed data (from the ``IDAT`` chunks).
This yields decompressed byte strings.

<a name="png.check_bitdepth_colortype"></a>
#### check\_bitdepth\_colortype

```python
check_bitdepth_colortype(bitdepth, colortype)
```

Check that `bitdepth` and `colortype` are both valid,
and specified in a valid combination.
Returns (None) if valid, raise an Exception if not valid.

<a name="png.is_natural"></a>
#### is\_natural

```python
is_natural(x)
```

A non-negative integer.

<a name="png.undo_filter_sub"></a>
#### undo\_filter\_sub

```python
undo_filter_sub(filter_unit, scanline, previous, result)
```

Undo sub filter.

<a name="png.undo_filter_up"></a>
#### undo\_filter\_up

```python
undo_filter_up(filter_unit, scanline, previous, result)
```

Undo up filter.

<a name="png.undo_filter_average"></a>
#### undo\_filter\_average

```python
undo_filter_average(filter_unit, scanline, previous, result)
```

Undo up filter.

<a name="png.undo_filter_paeth"></a>
#### undo\_filter\_paeth

```python
undo_filter_paeth(filter_unit, scanline, previous, result)
```

Undo Paeth filter.

<a name="png.convert_l_to_rgba"></a>
#### convert\_l\_to\_rgba

```python
convert_l_to_rgba(row, result)
```

Convert a grayscale image to RGBA.
This method assumes the alpha channel in result is
already correctly initialized.

<a name="png.convert_rgb_to_rgba"></a>
#### convert\_rgb\_to\_rgba

```python
convert_rgb_to_rgba(row, result)
```

Convert an RGB image to RGBA.
This method assumes the alpha channel in result is
already correctly initialized.

<a name="png.binary_stdin"></a>
#### binary\_stdin

```python
binary_stdin()
```

A sys.stdin that returns bytes.

<a name="png.binary_stdout"></a>
#### binary\_stdout

```python
binary_stdout()
```

A sys.stdout that accepts bytes.

<a name="png.main"></a>
#### main

```python
main(argv)
```

Run command line PNG.

