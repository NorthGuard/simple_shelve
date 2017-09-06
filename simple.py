import ast
import shelve
import textwrap
from collections import Mapping, deque
from pathlib import Path
from shelve import DbfilenameShelf

import os


class SimpleShelf(DbfilenameShelf):
    def __init__(self, path, replace=False, flag='c', protocol=None, writeback=False, internal_key_encoding="utf-8"):
        """
        Creates a shelf which is less particular about the types of the keys.
        :param Path | str path: Path to (create) shelf.
        :param bool replace: If true all data in an already-existing database will be removed.
        :param str flag: Argument for shelve.open()
        :param protocol: Argument for shelve.open()
        :param bool writeback: Argument for shelve.open()
        :param str internal_key_encoding: Decoding used for decoding internal key-strings to original keys.
        """
        path = path if isinstance(path, Path) else Path(path)
        self._path = path
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
        sorted_internal_keys = sorted(list(self.dict.keys()))
        keys = [self._2_external_key(key) for key in sorted_internal_keys]
        return keys

    def clear_and_remove(self):
        self.clear()
        for val in [".bak", ".dat", ".dir"]:
            try:
                os.remove(str(self._path) + val)
            except FileNotFoundError:
                pass
        del self

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
        if not isinstance(other, SimpleShelf):
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
            if isinstance(other, (Mapping, SimpleShelf)):
                args_other = [(self._2_external_key(key), other[key]) for key in other]
            elif hasattr(other, "keys"):
                args_other = [(self._2_external_key(key), other[key]) for key in other.keys()]
            else:
                args_other = [(self._2_external_key(key), value) for key, value in other]

        # Convert kwargs
        kwargs_other = {self._2_external_key(key): value for key, value in kwargs.items()}

        # Call super
        super().update(args_other, **kwargs_other)

    def setdefault(self, key, default=None):
        """"
        D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D
        """
        key = self._2_external_key(key)
        return super().setdefault(key=key, default=default)


class SimpleMultiShelf:
    def __init__(self, path, n_storages,
                 replace=False, flag='c', protocol=None, writeback=False, internal_key_encoding="utf-8"):
        """
        Creates multiple Python Shelf's and uses all of them for keeping items in (takes turn).
        This can be used as a quick fix for having larger datasets than what Python's Shelf allows.
        :param Path | str path: Path to base name file (multiple will be created).
        :param int n_storages: Number of storages to use.
        :param bool replace: If true all data in an already-existing database will be removed.
        :param str flag: Argument for shelve.open()
        :param protocol: Argument for shelve.open()
        :param bool writeback: Argument for shelve.open()
        :param str internal_key_encoding: Decoding used for decoding internal key-strings to original keys.
        """
        path = path if isinstance(path, Path) else Path(path)
        # Make storages
        self._n_storages = n_storages
        self._storage_paths = [Path(str(path) + "_" + str(val)) for val in range(n_storages)]
        self._storages = [SimpleShelf(path,
                                      replace=replace,
                                      flag=flag,
                                      protocol=protocol,
                                      writeback=writeback,
                                      internal_key_encoding=internal_key_encoding)
                          for path in self._storage_paths]

        # Key to database mapping
        self._key2database = dict()
        for idx, storage in enumerate(self._storages):
            keys = storage.keys_sorted()
            for key in keys:
                self._key2database[key] = idx

        # Storage with fewest items
        storage_lengths = [len(storage) for storage in self._storages]
        starting_index = storage_lengths.index(min(storage_lengths))
        self._storage_cycle = deque(range(n_storages))
        self._storage_cycle.rotate(-starting_index)

    def _next_storage_nr(self):
        nr = self._storage_cycle[0]
        self._storage_cycle.rotate(-1)
        return nr

    def _storage_w_key(self, key):
        return self._storages[self._key2database[key]]

    def keys_sorted(self):
        return sorted(self.keys())

    def clear_and_remove(self):
        for storage in self._storages:
            storage.clear_and_remove()
            del storage
        del self

    # Shelf

    def __setitem__(self, key, value):
        if key not in self:
            self._key2database[key] = self._next_storage_nr()
            self._storage_w_key(key)[key] = value

    def __iter__(self):
        for storage in self._storages:
            for key in storage.keys():
                yield key

    def __delitem__(self, key):
        del self._storage_w_key(key)[key]
        del self._key2database[key]

    def sync(self):
        for storage in self._storages:
            storage.sync()

    def close(self):
        for storage in self._storages:
            storage.close()

    def __enter__(self):
        return self

    def __exit__(self, exit_type, value, traceback):
        self.close()

    def __len__(self):
        return sum([len(storage) for storage in self._storages])

    def clear(self):
        for storage in self._storages:
            storage.clear()

    # Mapping

    def __getitem__(self, key):
        return self.get(key)

    def get(self, key, default=None):
        if key not in self._key2database:
            raise KeyError(f"'{key}' not in SimpleMultiShelf.")
        return self._storage_w_key(key).get(key, default=default)

    def __contains__(self, key):
        if key in self._key2database:
            return True
        return False

    def keys(self):
        return list(self)

    def items(self):
        item_list = []
        for storage in self._storages:
            item_list.extend(storage.items())
        return item_list

    def values(self):
        values = []
        for storage in self._storages:
            values.extend(storage.values())
        return values

    def __eq__(self, other):
        if not isinstance(other, SimpleMultiShelf):
            return NotImplemented
        return dict(self.items()) == dict(other.items())

    # MutableMapping

    def pop(self, key, default=None):
        val = self.get(key, default=default)
        del self[key]
        return val

    def popitem(self):
        storage_nr = self._storage_cycle[-1]
        self._storage_cycle.rotate(1)
        key, val = self._storages[storage_nr].popitem()
        del self._key2database[key]
        return key, val

    # # Implemented in MutableMapping
    def clear(self):
        for storage in self._storages:
            storage.clear()
        del self._key2database
        self._key2database = dict()

    def update(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError('update expected at most 1 arguments, got %d' %
                            len(args))

        # Convert args
        args_other = []
        if args:
            other = args[0]
            if isinstance(other, (Mapping, SimpleShelf)):
                args_other = [(key, other[key]) for key in other]
            elif hasattr(other, "keys"):
                args_other = [(key, other[key]) for key in other.keys()]
            else:
                args_other = [(key, value) for key, value in other]

        # Convert kwargs
        kwargs_other = [(key, value) for key, value in kwargs.items()]

        # Call super
        for key, val in args_other + kwargs_other:
            self[key] = val

    def setdefault(self, key, default=None):
        """"
        D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D
        """
        if key not in self:
            self[key] = default
        return self[key]

