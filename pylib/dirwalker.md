# Table of Contents

* [dirwalker](#dirwalker)
  * [DirWalkerBase](#dirwalker.DirWalkerBase)
    * [walk](#dirwalker.DirWalkerBase.walk)

<a name="dirwalker"></a>
# dirwalker

<a name="dirwalker.DirWalkerBase"></a>
## DirWalkerBase Objects

```python
class DirWalkerBase(object)
```

This abstract base class traverses all paths beginning with root,
calling its visit(path,files) method at each directory it encounters,
including root. If the constructor's follow_links parameter is True,
symbolic links are followed as well, and measures are taken to prevent
visiting the same "real" directory twice, so infinite loops are not a
problem.

As an abstract base class, DirWalkerBase will not allow itself to be
instantiated directly. You must subclass DirWalkerBase, providing your
own implementation of the constructor and visit methods. This gives
you great flexability in a way that fits the Python language very
naturally. DirWalkerBase.walk(root,follow_links) is the main engine of
this class and must be called if overridden in a subclass.

<a name="dirwalker.DirWalkerBase.walk"></a>
#### walk

```python
 | walk(root, follow_links=True)
```

Start walking the subdirectory tree at root, safely following
symlinks if follow_links is True (the default). For each path
visited, call the visit method with the name of the path and a list
of directory entries. The visit method may modify the list of
directory entries to cull them, but it must do so "in place".

