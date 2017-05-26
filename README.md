# Panasonic-viera TV control

A set of tools to control your Panasonic Viera TV.



## Usage

### Examples

#### Increase Volume By 1

```python
import panasonic_viera
rc = panasonic_viera.RemoteControl("<HOST>")
volume = rc.getVolume()
rc.setVolume(volume + 1)
```

#### Send EPG Key

```python
import panasonic_viera
rc = panasonic_viera.RemoteControl("<HOST>")
rc.sendKey(panasonic_viera.Keys.EPG)
```