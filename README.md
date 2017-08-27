# simple_shelve
Wrappings on Python's shelve-library for easier, key-type-independent access and databases which 
exceeds the shelve-size-limit.

### SimpleShelf

The `SimpleShelf`-class extends Python's Shelf-class and protects the database from non-string
input. Instead keys that are simple Python types will be converted to string for storage and 
returned to their original type when retrieved. 

Example:
```Python
# Create a simple shelf
print("Testing special keys.")

print("\nCreating SimpleShelf 'box'")
box = SimpleShelf(Path("box"), replace=True)

items = [
    ("a", "A"),
    (1, 2),
    (True, False),
    (3.4, 5.3),
    ((3, "a"), (1, "Tuple key")),
    ({1, 2, 3}, ("", "Set key (risky)")),
    ({1: "a", "b": 2}, (4.5, "Dict key (risky)")),
]

print("\nAdding various items:")
for a_key, a_val in items:
    print(f"\tbox[{str(a_key):^18s}] <- {str(a_val):25s}")
    box[a_key] = a_val

print(f"\nKeys: {box.keys()}")

print("\nRetrieving items:")
for a_key in box.keys():
    print(f"\tbox[{str(a_key):^18s}] -> {box[a_key]!s:25s} ({type(a_key).__name__})")
```

Produces:
```
Testing special keys.

Creating SimpleShelf 'box'

Adding various items:
	box[        a         ] <- A                        
	box[        1         ] <- 2                        
	box[       True       ] <- False                    
	box[       3.4        ] <- 5.3                      
	box[     (3, 'a')     ] <- (1, 'Tuple key')         
	box[    {1, 2, 3}     ] <- ('', 'Set key (risky)')  
	box[ {1: 'a', 'b': 2} ] <- (4.5, 'Dict key (risky)')
	
Keys: ['a', 1, True, 3.4, (3, 'a'), {1, 2, 3}, {1: 'a', 'b': 2}]

Retrieving items:
	box[        a         ] -> A                         (str)
	box[        1         ] -> 2                         (int)
	box[       True       ] -> False                     (bool)
	box[       3.4        ] -> 5.3                       (float)
	box[     (3, 'a')     ] -> (1, 'Tuple key')          (tuple)
	box[    {1, 2, 3}     ] -> ('', 'Set key (risky)')   (set)
	box[ {1: 'a', 'b': 2} ] -> (4.5, 'Dict key (risky)') (dict)
```

### MultiSimpleShelf

`MultiSimpleShelf` creates multiple Shelf's and cycles through them for storing objects.
This is a quick fix on how to avoid problems when the Shelf's database files becomes too big 
(in which case it throws an error).
