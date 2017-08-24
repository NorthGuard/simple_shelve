# simple_shelve
Wrappings on Python's shelve-library for easier, key-type-independent access and databases which 
exceeds the shelve-size-limit.

### SimpleShelf

The `SimpleShelf`-class extends Python's Shelf-class and protects the database from non-string
input. Instead keys that are simple Python types will be converted to string for storage and 
returned to their original type when retrieved. 

Example:
```Python
print("\nCreating SimpleShelf 'box'")
box = SimpleShelf(Path("box"), replace=True)

items = [
    ("a", "A"),
    (1, 2),
    (True, False),
    (3.4, 5.3)
]

print("\nAdding various items:")
for a_key, a_val in items:
    print(f"\tbox[{str(a_key):^5s}] <- {str(a_val):5s}")
    box[a_key] = a_val

print(f"\nKeys: {box.keys()}")

print("\nRetrieving items:")
for a_key in box.keys():
print(f"\tbox[{str(a_key):^5s}] -> {box[a_key]!s:5s} ({type(a_key).__name__})")
```

Produces:
```
Creating SimpleShelf 'box'

Adding various items:
	box[  a  ] <- A    
	box[  1  ] <- 2    
	box[True ] <- False
	box[ 3.4 ] <- 5.3  
	
Keys: ['a', 1, True, 3.4]

Retrieving items:
	box[  a  ] -> A     (str)
	box[  1  ] -> 2     (int)
	box[True ] -> False (bool)
	box[ 3.4 ] -> 5.3   (float)
```

### MultiSimpleShelf

`MultiSimpleShelf` creates multiple Shelf's and cycles through them for storing objects.
This is a quick fix on how to avoid problems when the Shelf's database files becomes too big 
(in which case it throws an error).
