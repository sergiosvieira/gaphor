# This file is generated by coder.py. DO NOT EDIT!
# ruff: noqa: F401, E402, F811
# fmt: off

from __future__ import annotations

from decimal import Decimal as UnlimitedNatural

from gaphor.core.modeling.properties import (
    association,
    attribute as _attribute,
    derived,
    derivedunion,
    enumeration as _enumeration,
    redefine,
    relation_many,
    relation_one,
)


from gaphor.UML.uml import Actor
class Person(Actor):
    description: _attribute[str] = _attribute("description", str)
    location: _attribute[str] = _attribute("location", str)


from gaphor.UML.uml import Package
class Container(Package):
    description: _attribute[str] = _attribute("description", str)
    location: _attribute[str] = _attribute("location", str)
    ownerContainer: relation_one[Container]
    owningContainer: relation_many[Container]
    technology: _attribute[str] = _attribute("technology", str)
    type: _attribute[str] = _attribute("type", str)


class Database(Container):
    pass


from gaphor.UML.uml import Dependency as _Dependency
class Dependency(_Dependency):
    technology: _attribute[str] = _attribute("technology", str)


from gaphor.UML.uml import Diagram
class C4Diagram(Diagram):
    diagramType: _attribute[str] = _attribute("diagramType", str, default="c4")



Container.ownerContainer = association("ownerContainer", Container, upper=1, opposite="owningContainer")
Container.owningContainer = association("owningContainer", Container, composite=True, opposite="ownerContainer")
from gaphor.UML.uml import NamedElement
NamedElement.namespace.add(Container.ownerContainer)  # type: ignore[attr-defined]
from gaphor.UML.uml import Namespace
Namespace.ownedMember.add(Container.owningContainer)  # type: ignore[attr-defined]
