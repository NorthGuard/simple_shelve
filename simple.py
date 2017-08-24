import ast
import shelve
from collections import Mapping
from pathlib import Path
from shelve import DbfilenameShelf


#
# class SimpleMultiShelf:
#     def __init__(self, paths):
#         self.storage_paths = paths
#         self.storages = [SimpleShelf(path) for path in paths]
#         self._key2database = dict()
#         for idx, storage in enumerate(self.storages):
#             keys = storage.keys_sorted()
#             for key in keys:
#                 self._key2database[key] = idx
#
#     def __getitem__(self, key):
#         return self.storages[self._key2database[key]][key]
#
#     def __setitem__(self, key, value):
#         self.storages[self._key2database[key]][key] = value
#
#     def __contains__(self, item):
#         for storage in self.storages:
#             if item in storage:
#                 return True
#         return False
#
#     def __delitem__(self, key):
#         del self.storages[self._key2database[key]][key]
#
#     def sync(self):
#         for storage in self.storages:
#             storage.sync()
#
#     def keys(self):
#         keys = set()
#         for storage in self.storages:
#             keys.update(storage.keys())
#         return list(keys)
#
#     def close(self):
#         for storage in self.storages:
#             storage.close()
#
#     def __len__(self):
#         return np.array([len(storage) for storage in self.storages]).sum()


class SimpleShelf2(DbfilenameShelf):
    def __init__(self, path, replace=False, flag='c', protocol=None, writeback=False, internal_key_encoding="utf-8"):
        super().__init__(filename=str(path), flag=flag, protocol=protocol, writeback=writeback)
        if replace:
            self.clear()
        self._internal_key_encoding = internal_key_encoding

    @staticmethod
    def _2_internal_key(key):
        return str(key)

    def _2_external_key(self, key):
        if isinstance(key, bytes):
            key = key.decode(self._internal_key_encoding)
        try:
            return ast.literal_eval(key)
        except (ValueError, SyntaxError):
            return key

    def keys_sorted(self):
        """
        Properly sort the keys so that the integer 2 and the string '2' will be close to each other etc.
        :return:
        """
        # TODO: Can be written more efficiently
        keys = [(self._2_internal_key(key), isinstance(key, str)) for key in self.keys()]
        keys.sort(key=lambda x: x[0])
        keys = [(self._2_external_key(key) if not was_string else key) for key, was_string in keys]
        return keys

    # Shelf

    def __setitem__(self, key, value):
        key = self._2_internal_key(key)
        super().__setitem__(key=key, value=value)

    def __iter__(self):
        for key in super().__iter__():
            yield self._2_external_key(key)

    def __delitem__(self, key):
        key = self._2_internal_key(key)
        super().__delitem__(key=key)

    # Mapping

    def __getitem__(self, key):
        key = self._2_internal_key(key)
        return super().__getitem__(key=key)

    def get(self, key, default=None):
        key = self._2_internal_key(key)
        return super().get(key=key, default=default)

    def __contains__(self, key):
        key = self._2_internal_key(key)
        return super().__contains__(key=key)

    def keys(self):
        return [self._2_external_key(key) for key in self.dict.keys()]

    def items(self):
        return [(self._2_external_key(key), val)
                for key, val in super().items()]

    def values(self):
        return list(super().values())

    def __eq__(self, other):
        if not isinstance(other, SimpleShelf2):
            return NotImplemented
        return dict(self.items()) == dict(other.items())

    # MutableMapping

    __marker = object()

    def pop(self, key, default=__marker):
        key = self._2_internal_key(key)
        return super().pop(key=key, default=default)

    def popitem(self):
        key, val = super().popitem()
        key = self._2_external_key(key)
        return key, val

    # Implemented in MutableMapping
    def clear(self):
        """
        D.clear() -> None.  Remove all items from D.
        """
        try:
            while True:
                self.popitem()
        except KeyError:
            pass

    def update(self, *args, **kwargs):
        """
        D.update([E, ]**F) -> None.  Update D from mapping/iterable E and F.
        If E present and has a .keys() method, does:     for k in E: D[k] = E[k]
        If E present and lacks .keys() method, does:     for (k, v) in E: D[k] = v
        In either case, this is followed by: for k, v in F.items(): D[k] = v
        """
        if len(args) > 1:
            raise TypeError('update expected at most 1 arguments, got %d' %
                            len(args))

        # Convert args
        args_other = []
        if args:
            other = args[0]
            if isinstance(other, (Mapping, SimpleShelf2)):
                for key in other:
                    args_other.append((self._2_external_key(key), other[key]))
            elif hasattr(other, "keys"):
                for key in other.keys():
                    args_other.append((self._2_external_key(key), other[key]))
            else:
                for key, value in other:
                    args_other.append((self._2_external_key(key), value))

        # Convert kwargs
        kwargs_other = dict()
        for key, value in kwargs.items():
            kwargs_other[self._2_external_key(key)] = value

        # Call super
        super().update(self, args_other, **kwargs_other)

    def setdefault(self, key, default=None):
        """"
        D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D
        """
        key = self._2_external_key(key)
        return super().setdefault(key=key, default=default)


if __name__ == "__main__":
    line = "------------------------------------------------"

    # Create a simple shelf
    print(line)
    print("Testing special keys.")

    print("\nCreating SimpleShelf 'box'")
    box = SimpleShelf2(Path("box"), replace=True)

    items = [
        ("a", "A"),
        (1, 2),
        (True, False),
        (3.4, 5.3)
    ]

    print("\nAdding various items:")
    for a_key, a_val in items:
        print(f"\tbox[{str(a_key):^5s}] <- {str(a_val)}")
        box[a_key] = a_val

    print(f"\nKeys: {box.keys()}")

    print("\nRetrieving items:")
    for a_key in box.keys():
        print(f"\tbox[{str(a_key):^5s}] -> {box[a_key]}")

    ########################################################################
    print("\n\n" + line)
    print("Testing side by side commands of SimpleShelf and Shelf")
    box.clear()

    print("\nCreating Shelf 'box2'")
    box2 = shelve.open("box2")

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

    print("\nDone. ")

