# Copyright (C) 2012 - 2020  Christian Ledermann
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

"""Abstract base classes"""
import logging
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import cast

from fastkml import config
from fastkml.enums import Verbosity
from fastkml.helpers import o_from_attr
from fastkml.helpers import o_to_attr
from fastkml.types import Element
from fastkml.types import KmlObjectMap

logger = logging.getLogger(__name__)


class _XMLObject:
    """XML Baseclass."""

    _namespaces: Tuple[str, ...] = ("",)
    _node_name: str = ""
    __name__ = ""
    kml_object_mapping: Tuple[KmlObjectMap, ...] = ()

    def __init__(self, ns: Optional[str] = None) -> None:
        """Initialize the XML Object."""
        self.ns: str = self._namespaces[0] if ns is None else ns

    def __eq__(self, other: object) -> bool:
        """Compare two XML Objects."""
        if not isinstance(other, self.__class__):
            return False
        return (
            other.ns == self.ns or other.ns in self._namespaces
            if self.ns == ""
            else True
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(ns={self.ns})"

    def __str__(self) -> str:
        return self.to_string()

    def etree_element(
        self,
        precision: Optional[int] = None,
        verbosity: Verbosity = Verbosity.normal,
    ) -> Element:
        """Return the KML Object as an Element."""
        if self.__name__:
            element: Element = config.etree.Element(  # type: ignore[attr-defined]
                f"{self.ns}{self.__name__}"
            )
        else:
            raise NotImplementedError(
                "Call of abstract base class, subclasses implement this!"
            )
        for mapping in self.kml_object_mapping:
            mapping["to_kml"](self, element, **mapping)
        return element

    def from_element(self, element: Element) -> None:
        """
        Load the KML Object from an Element.

        This implementation is deprecated and will be replaced by class_from_element
        making it a classmethod.
        """
        if f"{self.ns}{self.__name__}" != element.tag:
            raise TypeError("Call of abstract base class, subclasses implement this!")
        for mapping in self.kml_object_mapping:
            mapping["from_kml"](self, element, **mapping)

    def from_string(self, xml_string: str) -> None:
        """
        Load the KML Object from serialized xml.

        This implementation is deprecated and will be replaced by class_from_string
        making it a classmethod.
        """
        self.from_element(
            cast(Element, config.etree.XML(xml_string))  # type: ignore[attr-defined]
        )

    def to_string(
        self,
        *,
        prettyprint: bool = True,
        precision: Optional[int] = None,
        verbosity: Verbosity = Verbosity.normal,
    ) -> str:
        """Return the KML Object as serialized xml."""
        try:
            return cast(
                str,
                config.etree.tostring(  # type: ignore[attr-defined]
                    self.etree_element(
                        precision=precision,
                        verbosity=verbosity,
                    ),
                    encoding="UTF-8",
                    pretty_print=prettyprint,
                ).decode("UTF-8"),
            )
        except TypeError:
            return cast(
                str,
                config.etree.tostring(  # type: ignore[attr-defined]
                    self.etree_element(), encoding="UTF-8"
                ).decode("UTF-8"),
            )

    @classmethod
    def _get_ns(cls, ns: Optional[str]) -> str:
        return cls._namespaces[0] if ns is None else ns

    @classmethod
    def _get_kwargs(
        cls,
        *,
        ns: str,
        element: Element,
        strict: bool,
    ) -> Dict[str, Any]:
        """Returns a dictionary of kwargs for the class constructor."""
        kwargs: Dict[str, Any] = {}
        return kwargs

    @classmethod
    def class_from_element(
        cls,
        *,
        ns: str,
        element: Element,
        strict: bool,
    ) -> "_XMLObject":
        """Creates an XML object from an etree element."""
        kwargs = cls._get_kwargs(ns=ns, element=element, strict=strict)
        return cls(
            ns=ns,
            **kwargs,
        )

    @classmethod
    def class_from_string(
        cls,
        string: str,
        *,
        ns: Optional[str] = None,
        strict: bool = True,
    ) -> "_XMLObject":
        """Creates a geometry object from a string.

        Args:
            string: String representation of the geometry object

        Returns:
            Geometry object
        """
        ns = cls._get_ns(ns)
        return cls.class_from_element(
            ns=ns,
            strict=strict,
            element=cast(
                Element,
                config.etree.fromstring(string),  # type: ignore[attr-defined]
            ),
        )


class _BaseObject(_XMLObject):
    """
    Base class for all KML objects.

    This is an abstract base class and cannot be used directly in a
    KML file. It provides the id attribute, which allows unique
    identification of a KML element, and the targetId attribute,
    which is used to reference objects that have already been loaded into
    Google Earth. The id attribute must be assigned if the <Update>
    mechanism is to be used.
    """

    _namespace = config.KMLNS
    _namespaces: Tuple[str, ...] = (config.KMLNS,)

    id = None
    target_id = None
    kml_object_mapping: Tuple[KmlObjectMap, ...] = (
        {
            "kml_attr": "id",
            "obj_attr": "id",
            "from_kml": o_from_attr,
            "to_kml": o_to_attr,
            "required": False,
            "validator": None,
        },
        {
            "kml_attr": "targetId",
            "obj_attr": "target_id",
            "from_kml": o_from_attr,
            "to_kml": o_to_attr,
            "required": False,
            "validator": None,
        },
    )

    def __init__(
        self,
        ns: Optional[str] = None,
        id: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> None:
        """Initialize the KML Object."""
        super().__init__(ns)
        self.id = id
        self.target_id = target_id

    def __eq__(self, other: object) -> bool:
        assert isinstance(other, self.__class__)
        return (
            super().__eq__(other)
            and self.id == other.id
            and self.target_id == other.target_id
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(ns={self.ns!r}, "
            f"(id={self.id!r}, target_id={self.target_id!r})"
        )

    def etree_element(
        self,
        precision: Optional[int] = None,
        verbosity: Verbosity = Verbosity.normal,
    ) -> Element:
        """Return the KML Object as an Element."""
        return super().etree_element(precision=precision, verbosity=verbosity)

    def from_element(self, element: Element) -> None:
        """Load the KML Object from an Element."""
        super().from_element(element)

    @classmethod
    def _get_id(cls, element: Element, strict: bool) -> str:
        return element.get("id") or ""

    @classmethod
    def _get_target_id(cls, element: Element, strict: bool) -> str:
        return element.get("targetId") or ""

    @classmethod
    def _get_kwargs(
        cls,
        *,
        ns: str,
        element: Element,
        strict: bool,
    ) -> Dict[str, Any]:
        """Get the keyword arguments to build the object from an element."""
        return {
            "id": cls._get_id(element=element, strict=strict),
            "target_id": cls._get_target_id(element=element, strict=strict),
        }
