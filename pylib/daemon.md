# Table of Contents

* [daemon](#daemon)
  * [DaemonContext](#daemon.DaemonContext)
    * [terminate](#daemon.DaemonContext.terminate)
    * [open](#daemon.DaemonContext.open)
    * [close](#daemon.DaemonContext.close)

<a name="daemon"></a>
# daemon

<a name="daemon.DaemonContext"></a>
## DaemonContext Objects

```python
class DaemonContext(object)
```

This is an implementation of PEP-3143.

<a name="daemon.DaemonContext.terminate"></a>
#### terminate

```python
 | terminate(sig, stack)
```

This is called if we get SIGTERM (typically).

<a name="daemon.DaemonContext.open"></a>
#### open

```python
 | open()
```

Go daemon.

<a name="daemon.DaemonContext.close"></a>
#### close

```python
 | close()
```

Politely close this DaemonContext (if it's open).

