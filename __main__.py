import shelve
from pathlib import Path

from simple_shelve import SimpleShelf, SimpleMultiShelf


line = "------------------------------------------------"

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


########################################################################
print("\n\n" + line)
print("Testing side by side commands of SimpleShelf and Shelf")
box.clear()

print("\nCreating Shelf 'box2'")
box2 = shelve.open("box2")
box2.clear()

print("\nbox")
print(box.keys())
print("box2")
print(list(box2.keys()))

box["a"] = "A"
box2["a"] = "A"
box["b"] = "B"
box2["b"] = "B"
box["c"] = "C"
box2["c"] = "C"

print("\nbox")
print(box.items())
print("box2")
print(list(box2.items()))

print("\nbox")
print("a" in box)
print("box2")
print("a" in box2)

del box["b"]
del box2["b"]

print("\nbox")
print(box.popitem())
print("box2")
print(list(box2.popitem()))

print("\nbox")
print(box.items())
print("box2")
print(list(box2.items()))


########################################################################
print("\n\n" + line)
print("Testing MultiSimpleShelf")

multi_shelf = SimpleMultiShelf("multi_shelf", n_storages=3, replace=True)

for char in range(97, 97 + 26):
    char = chr(char)
    multi_shelf[char] = char.capitalize()

print(f"MultiSimpleShelf keys: {multi_shelf.keys()}")

multi_shelf.pop("c")
print(f"popitem: {multi_shelf.popitem()}")
print(f"MultiSimpleShelf items: {multi_shelf.items()}")
print(f"MultiSimpleShelf values: {multi_shelf.values()}")

########################################################################
print("\n\n" + line)
print("Removing files")

box.clear_and_remove()
multi_shelf.clear_and_remove()
del box2
box2 = SimpleShelf("box2")
box2.clear_and_remove()

print("\nDone. ")
