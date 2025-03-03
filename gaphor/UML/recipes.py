"""UML model support functions.

Functions collected in this module allow to

- create more complex UML model structures
- perform specific searches and manipulations
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Iterable, Sequence
from decimal import Decimal as UnlimitedNatural
from typing import TypeVar

from gaphor.UML.uml import (
    Artifact,
    Association,
    Class,
    Classifier,
    Component,
    ConnectableElement,
    Connector,
    ConnectorEnd,
    DataType,
    Dependency,
    Element,
    Extension,
    ExtensionEnd,
    Generalization,
    InstanceSpecification,
    Interface,
    LiteralBoolean,
    LiteralInteger,
    LiteralString,
    LiteralUnlimitedNatural,
    Message,
    MessageOccurrenceSpecification,
    MultiplicityElement,
    Package,
    Parameter,
    Port,
    Property,
    Realization,
    Slot,
    Stereotype,
    StructuralFeature,
    StructuredClassifier,
    Type,
    Usage,
    ValueSpecification,
)

T = TypeVar("T", bound=Element)


def stereotypes_str(element: Element, stereotypes: Sequence[str] = ()) -> str:
    """Identify stereotypes of a UML metamodel instance and return coma
    separated stereotypes as string.

    :Parameters:
     element
        Element having stereotypes, can be None.
     stereotypes
        List of additional stereotypes, can be empty.
    """
    # generate string with stereotype names separated by coma
    if element:
        applied: Iterable[str] = (
            stereotype_name(st) for st in get_applied_stereotypes(element)
        )
    else:
        applied = ()
    if s := ", ".join(itertools.chain(stereotypes, applied)):
        return f"«{s}»"
    return ""


def stereotype_name(stereotype: Stereotype) -> str:
    """Return stereotype name suggested by UML specification. First will be
    character lowercase unless the second character is uppercase.

    :Parameters:
     stereotype
        Stereotype UML metamodel instance.
    """
    name: str = stereotype.name
    if not name:
        return ""
    elif len(name) > 1 and name[1].isupper():
        return name
    return name[0].lower() + name[1:]


def apply_stereotype(element: Element, stereotype: Stereotype) -> InstanceSpecification:
    """Apply a stereotype to an element.

    :Parameters:
     element
        UML metamodel class instance.
     stereotype
        UML metamodel stereotype instance.
    """
    assert element.model is stereotype.model, (
        "Element and Stereotype are from different models"
    )
    model = element.model
    obj = model.create(InstanceSpecification)
    obj.classifier = stereotype
    element.appliedStereotype = obj
    return obj


def remove_stereotype(element: Element, stereotype: Stereotype) -> None:
    """Remove a stereotype from an element.

    :Parameters:
     element
        UML metamodel element instance.
     stereotype
        UML metamodel stereotype instance.
    """
    for obj in element.appliedStereotype:
        assert isinstance(obj, InstanceSpecification)
        if obj.classifier and obj.classifier[0] is stereotype:
            del element.appliedStereotype[obj]
            obj.unlink()
            break


def get_stereotypes(element: Element) -> list[Stereotype]:
    """Get sorted collection of possible stereotypes for specified element."""
    model = element.model
    # UML specs does not allow to extend stereotypes with stereotypes
    if isinstance(element, Stereotype):
        return []

    cls = type(element)

    # find out names of classes, which are superclasses of element class
    names = {c.__name__ for c in cls.__mro__ if issubclass(c, Element)}

    # find stereotypes that extend element class
    classes: Iterable[Class] = model.select(  # type: ignore[assignment]
        lambda e: isinstance(e, Class) and e.name in names
    )

    stereotypes = list({ext.ownedEnd.type for cls in classes for ext in cls.extension})

    all_stereotypes = stereotypes
    for s in stereotypes:
        for sub in s.specialization[:].specific:
            if isinstance(sub, Stereotype) and sub not in all_stereotypes:
                all_stereotypes.append(sub)

    return sorted(all_stereotypes, key=lambda st: st.name)


def get_applied_stereotypes(element: Element) -> Sequence[Stereotype]:
    """Get collection of applied stereotypes to an element."""
    return (
        element.appliedStereotype[:].classifier if isinstance(element, Element) else []  # type: ignore[return-value]
    )


def create_extension(metaclass: Class, stereotype: Stereotype) -> Extension:
    """Create an Extension association between a metaclass and a stereotype."""
    assert metaclass.model is stereotype.model, (
        "Metaclass and Stereotype are from different models"
    )

    model = metaclass.model
    ext: Extension = model.create(Extension)
    p = model.create(Property)
    ext_end = model.create(ExtensionEnd)

    ext.memberEnd = p
    ext.memberEnd = ext_end
    ext.ownedEnd = ext_end
    ext_end.type = stereotype
    ext_end.aggregation = "composite"
    p.type = metaclass
    p.name = "baseClass"
    stereotype.ownedAttribute = p
    metaclass.ownedAttribute = ext_end

    return ext


def is_metaclass(element: Element) -> bool:
    return (
        (not isinstance(element, Stereotype))
        and hasattr(element, "extension")
        and bool(element.extension)
    )


def add_slot(
    instance: InstanceSpecification, definingFeature: StructuralFeature
) -> Slot:
    """Add slot to instance specification for an attribute."""
    assert instance.model is definingFeature.model, (
        "Instance and Defining feature are from different models"
    )
    model = instance.model
    slot = model.create(Slot)
    slot.definingFeature = definingFeature
    instance.slot = slot
    return slot


def get_slot_value(slot: Slot) -> str | None:
    """Get slot value as a string."""
    if slot.value is None:
        return None
    if isinstance(slot.value, LiteralString):
        return str(slot.value.value)
    return None


def set_slot_value(slot: Slot, value: str) -> None:
    """Set slot value to a string."""
    if slot.value:
        slot.value.unlink()
    slot_value = slot.model.create(LiteralString)
    slot.value = slot_value
    slot_value.owningSlot = slot
    slot_value.value = value


def create_dependency(supplier, client):
    assert supplier.model is client.model, (
        "Supplier and Client are from different models"
    )
    model = supplier.model
    dep = model.create(Dependency)
    dep.supplier = supplier
    dep.client = client
    return dep


def create_realization(realizingClassifier, abstraction):
    assert realizingClassifier.model is abstraction.model, (
        "Realizing classifier and Abstraction are from different models"
    )
    model = realizingClassifier.model
    dep = model.create(Realization)
    dep.realizingClassifier = realizingClassifier
    dep.abstraction = abstraction
    return dep


def create_generalization(general, specific):
    assert general.model is specific.model, (
        "General and Specific are from different models"
    )
    model = general.model
    gen = model.create(Generalization)
    gen.general = general
    gen.specific = specific
    return gen


def create_association(type_a: Type, type_b: Type):
    """Create an association between two items."""
    assert type_a.model is type_b.model, "Head and Tail end are from different models"
    model = type_a.model
    assoc = model.create(Association)
    end_a = model.create(Property)
    end_b = model.create(Property)
    end_a.association = assoc
    end_b.association = assoc
    end_a.type = type_a
    end_b.type = type_b
    # set default navigability (unknown)
    set_navigability(assoc, end_a, None)
    set_navigability(assoc, end_b, None)
    return assoc


def create_connector(
    type_a: ConnectableElement, type_b: ConnectableElement
) -> Connector:
    """Create a connector between two items.

    Depending on the ends, the connector kind may be "assembly" or
    "delegation".
    """
    assert type_a.model is type_b.model, "Head and Tail end are from different models"
    model = type_a.model
    conn = model.create(Connector)
    end_a = model.create(ConnectorEnd)
    end_b = model.create(ConnectorEnd)

    conn.end = end_a
    conn.end = end_b

    end_a.role = type_a
    end_b.role = type_b

    if (isinstance(end_a, Port) and isinstance(end_b, Property)) or (
        isinstance(end_a, Property) and isinstance(end_b, Port)
    ):
        conn.kind = "delegation"
    else:
        conn.kind = "assembly"

    return conn


TYPES_WITH_OWNED_ATTRIBUTE = (
    Artifact,
    Class,
    DataType,
    Interface,
    StructuredClassifier,
)


def set_navigability(assoc: Association, end: Property, nav: bool | None) -> None:
    """Set navigability of an association end (property).

    There are three possible values for ``nav`` parameter:
    1. True - association end is navigable
    2. False - association end is not navigable
    3. None - association end navigability is unknown

    There are two ways of specifying that an end is navigable:
    - an end is in Association.navigableOwnedEnd collection
    - an end is class (interface) attribute (stored in Class.ownedAttribute
      collection)

    Let's consider the graph::

        A -----> B
          y    x

    There two association ends A.x and B.y, A.x is navigable.

    Therefore, we construct navigable association ends in the following way:

    - if A is a class or an interface, then A.x is an attribute owned by A
    - if A is other classifier, then association is more general
      relationship; it may mean that participating instance of B can be
      "accessed efficiently"
      - i.e. when A is a Component, then association may be some compositing
        relationship
      - when A and B are instances of Node class, then it is a
        communication path

    Therefore, we store the navigable association end as one of the following:
    - {Class,Interface}.ownedAttribute due to their capabilities of
      editing owned members
    - Association.navigableOwnedEnd

    When an end has unknown (unspecified) navigability, then it is owned by
    association (but not by classifier).

    When an end is non-navigable, then it is just member of an association.
    """
    assert end.opposite
    owner = end.opposite.type
    # remove "navigable" and "unspecified" navigation indicators first
    if isinstance(owner, TYPES_WITH_OWNED_ATTRIBUTE) and end in owner.ownedAttribute:
        owner.ownedAttribute.remove(end)
    if end in assoc.ownedEnd:
        assoc.ownedEnd.remove(end)
    if end in assoc.navigableOwnedEnd:
        assoc.navigableOwnedEnd.remove(end)

    assert end not in assoc.ownedEnd
    assert end not in assoc.navigableOwnedEnd

    if nav is True:
        if isinstance(owner, TYPES_WITH_OWNED_ATTRIBUTE):
            owner.ownedAttribute = end
        else:
            assoc.navigableOwnedEnd = end
    elif nav is None:
        assoc.ownedEnd = end
    # elif nav is False, non-navigable


def dependency_type(client, supplier):
    """Determine dependency type between client (tail) and supplier
    (arrowhead).

    There can be different dependencies detected automatically

    - usage when supplier is an interface
    - realization when client is component and supplier is a classifier

    If none of above is detected then standard dependency is determined.
    """
    dt = Dependency

    # test interface first as it is a classifier
    if isinstance(supplier, Interface):
        dt = Usage
    elif (
        isinstance(supplier, Component)
        and isinstance(client, Classifier)
        and not isinstance(client, Component)
    ):
        dt = Realization

    return dt


def clone_message(msg, inverted=False):
    """Create new message based on specified message.

    If inverted is set to True, then inverted message is created.
    """
    model = msg.model
    message = model.create(Message)
    send = None
    receive = None

    if msg.sendEvent:
        send = model.create(MessageOccurrenceSpecification)
        send.covered = msg.sendEvent.covered
    if msg.receiveEvent:
        receive = model.create(MessageOccurrenceSpecification)
        receive.covered = msg.receiveEvent.covered

    if inverted:
        # inverted message goes in different direction, then the original message
        message.sendEvent = receive
        message.receiveEvent = send
    else:
        message.sendEvent = send
        message.receiveEvent = receive
    return message


def owner_of_type(element: Element | None, owner_type: type[T]) -> T | None:
    if element is None or isinstance(element, owner_type):
        return element
    return owner_of_type(element.owner, owner_type)


def owner_package(element: Element | None) -> Package | None:
    return owner_of_type(element, Package)


def get_property_default_value(property: Property) -> ValueSpecification:
    """Get default value of a property."""
    return property.defaultValue


def get_property_default_value_as_string(property: Property) -> str | None:
    """Get default value of a property as a string."""
    if property.defaultValue is None:
        return None
    return get_literal_value_as_string(property.defaultValue)


def get_literal_value_as_string(value: ValueSpecification) -> str | None:
    """Get literal value as a string."""
    if value is None:
        return None
    if isinstance(value, LiteralUnlimitedNatural):
        if math.isinf(value.value):
            return "*"
        return str(int(value.value))
    if isinstance(value, LiteralInteger):
        return str(value.value)
    if isinstance(value, LiteralString):
        return str(value.value)
    if isinstance(value, LiteralBoolean):
        if value.value is True:
            return "true"
        return "false"
    return None


def set_property_default_value_from_string(
    property: Property, value: str | None
) -> None:
    """Set default value of a property."""
    if property.defaultValue:
        property.defaultValue.unlink()
    if value is None:
        return
    default_value = create_value_specification_for_type_and_value(
        property.model, property.typeValue, value
    )
    property.defaultValue = default_value
    if default_value is not None:
        default_value.owningProperty = property


def create_value_specification_for_type_and_value(
    model, type: str | None, value: str | None
) -> ValueSpecification | None:
    if value is None:
        return None
    if type is None:
        if value == "true" or value == "false":
            type = "bool"
        elif value.isnumeric():
            type = "int"
        else:
            type = "str"
    value_specification = None
    match type:
        case "bool" | "Boolean":
            value_specification = model.create(LiteralBoolean)
            if value == "true":
                value_specification.value = True
                value_specification.name = "true"
            else:
                value_specification.value = False
                value_specification.name = "false"
        case "str" | "String":
            stripped_value = value.replace('"', "")
            value_specification = model.create(LiteralString)
            value_specification.value = value
            value_specification.name = stripped_value
        case "int" | "Integer":
            value_specification = model.create(LiteralInteger)
            value_specification.value = int(value)
            value_specification.name = value
        case "UnlimitedNatural":
            value_specification = model.create(LiteralUnlimitedNatural)
            if value == "*":
                value_specification.value = UnlimitedNatural(math.inf)
                value_specification.name = "*"
            else:
                value_specification.value = UnlimitedNatural(int(value))
                value_specification.name = value
        # case "float" | "Real":
        #     value_specification = model.create(LiteralReal)
        #     value_specification.value = float(value)
    return value_specification


def get_property_lower_value(property: Property) -> int | None:
    """Get lower value of a property."""
    if property.lowerValue is None:
        return None
    if isinstance(property.lowerValue, LiteralInteger):
        return int(property.lowerValue.value)
    return None


def get_property_lower_value_as_string(property: Property) -> str | None:
    """Get lower value of a property as a string."""
    if property.lowerValue is None:
        return None
    if isinstance(property.lowerValue, LiteralInteger):
        return str(property.lowerValue.value)
    return None


def set_property_lower_value(property: Property, value: int | None) -> None:
    """Set lower value of a property."""
    if property.lowerValue:
        property.lowerValue.unlink()
    if value is None:
        return
    lower_value = property.model.create(LiteralInteger)
    property.lowerValue = lower_value
    lower_value.owningLower = property
    property.lowerValue.value = value
    property.lowerValue.name = str(value)


def set_property_lower_value_from_string(property: Property, value: str | None) -> None:
    """Set lower value of a property from a string."""
    if property.lowerValue:
        property.lowerValue.unlink()
    if value is None:
        return
    lower_value = property.model.create(LiteralInteger)
    property.lowerValue = lower_value
    lower_value.owningLower = property
    property.lowerValue.value = int(value)
    property.lowerValue.name = value


def get_property_upper_value(property: Property) -> UnlimitedNatural | None:
    """Get upper value of a property."""
    if property.upperValue is None:
        return None
    if isinstance(property.upperValue, LiteralUnlimitedNatural):
        return UnlimitedNatural(property.upperValue.value)
    return None


def get_property_upper_value_as_string(property: Property) -> str | None:
    """Get upper value of a property as a string."""
    if property.upperValue is None:
        return None
    if isinstance(property.upperValue, LiteralUnlimitedNatural):
        if math.isinf(property.upperValue.value):
            return "*"
        return str(int(property.upperValue.value))
    return None


def set_property_upper_value(
    property: Property, value: UnlimitedNatural | None
) -> None:
    """Set upper value of a property."""
    if property.upperValue:
        property.upperValue.unlink()
    if value is None:
        return
    upper_value = property.model.create(LiteralUnlimitedNatural)
    property.upperValue = upper_value
    upper_value.owningUpper = property
    property.upperValue.value = value
    if math.isinf(value):
        property.upperValue.name = "*"
    else:
        property.upperValue.name = str(int(value))


def set_property_upper_value_from_string(property: Property, value: str | None) -> None:
    """Set upper value of a property from a string."""
    if property.upperValue:
        property.upperValue.unlink()
    if value is None:
        return
    upper_value = property.model.create(LiteralUnlimitedNatural)
    property.upperValue = upper_value
    upper_value.owningUpper = property
    if value == "*":
        property.upperValue.value = UnlimitedNatural(math.inf)
    else:
        property.upperValue.value = UnlimitedNatural(int(value))
    property.upperValue.name = value


def get_multiplicity_lower_value(multiplicity: MultiplicityElement) -> int | None:
    """Get lower value of a multiplicity."""
    if multiplicity.lowerValue is None:
        return None
    if isinstance(multiplicity.lowerValue, LiteralInteger):
        return int(multiplicity.lowerValue.value)
    return None


def get_multiplicity_lower_value_as_string(
    multiplicity: MultiplicityElement,
) -> str | None:
    """Get lower value of a multiplicity as a string."""
    if multiplicity.lowerValue is None:
        return None
    if isinstance(multiplicity.lowerValue, LiteralInteger):
        return str(multiplicity.lowerValue.value)
    return None


def set_multiplicity_lower_value(
    multiplicity: MultiplicityElement, value: int | None
) -> None:
    """Set lower value of a multiplicity."""
    if multiplicity.lowerValue:
        multiplicity.lowerValue.unlink()
    if value is None:
        return
    lower_value = multiplicity.model.create(LiteralInteger)
    multiplicity.lowerValue = lower_value
    lower_value.owningLower = multiplicity
    multiplicity.lowerValue.value = value
    multiplicity.lowerValue.name = str(value)


def set_multiplicity_lower_value_from_string(
    multiplicity: MultiplicityElement, value: str | None
) -> None:
    """Set lower value of a multiplicity from a string."""
    if multiplicity.lowerValue:
        multiplicity.lowerValue.unlink()
    if value is None:
        return
    lower_value = multiplicity.model.create(LiteralInteger)
    multiplicity.lowerValue = lower_value
    lower_value.owningLower = multiplicity
    multiplicity.lowerValue.value = int(value)
    multiplicity.lowerValue.name = value


def get_multiplicity_upper_value(
    multiplicity: MultiplicityElement,
) -> UnlimitedNatural | None:
    """Get upper value of a multiplicity."""
    if multiplicity.upperValue is None:
        return None
    if isinstance(multiplicity.upperValue, LiteralUnlimitedNatural):
        return UnlimitedNatural(multiplicity.upperValue.value)
    return None


def get_multiplicity_upper_value_as_string(
    multiplicity: MultiplicityElement,
) -> str | None:
    """Get upper value of a multiplicity as a string."""
    if multiplicity.upperValue is None:
        return None
    if isinstance(multiplicity.upperValue, LiteralUnlimitedNatural):
        if math.isinf(multiplicity.upperValue.value):
            return "*"
        return str(int(multiplicity.upperValue.value))
    return None


def set_multiplicity_upper_value(
    multiplicity: MultiplicityElement, value: UnlimitedNatural | None
) -> None:
    """Set upper value of a multiplicity."""
    if multiplicity.upperValue:
        multiplicity.upperValue.unlink()
    if value is None:
        return
    upper_value = multiplicity.model.create(LiteralUnlimitedNatural)
    multiplicity.upperValue = upper_value
    upper_value.owningUpper = multiplicity
    multiplicity.upperValue.value = value
    if math.isinf(value):
        multiplicity.upperValue.name = "*"
    else:
        multiplicity.upperValue.name = str(int(value))


def set_multiplicity_upper_value_from_string(
    multiplicity: MultiplicityElement, value: str | None
) -> None:
    """Set upper value of a multiplicity from a string."""
    if multiplicity.upperValue:
        multiplicity.upperValue.unlink()
    if value is None:
        return
    upper_value = multiplicity.model.create(LiteralUnlimitedNatural)
    multiplicity.upperValue = upper_value
    upper_value.owningUpper = multiplicity
    if value == "*":
        multiplicity.upperValue.value = UnlimitedNatural(math.inf)
    else:
        multiplicity.upperValue.value = UnlimitedNatural(int(value))
    multiplicity.upperValue.name = value


def get_parameter_default_value(parameter: Parameter) -> ValueSpecification | None:
    """Get default value of a parameter."""
    return parameter.defaultValue


def get_parameter_default_value_as_string(parameter: Parameter) -> str | None:
    """Get default value of a parameter as a string."""
    if parameter.defaultValue is None:
        return None
    return get_literal_value_as_string(parameter.defaultValue)


def set_parameter_default_value(
    parameter: Parameter, value: ValueSpecification | None
) -> None:
    """Set default value of a parameter."""
    if parameter.defaultValue:
        parameter.defaultValue.unlink()
    if value is None:
        return
    parameter.defaultValue = value
    value.owningParameter = parameter


def set_parameter_default_value_from_string(
    parameter: Parameter, value: str | None
) -> None:
    """Set default value of a parameter."""
    if parameter.defaultValue:
        parameter.defaultValue.unlink()
    if value is None:
        return
    default_value = create_value_specification_for_type_and_value(
        parameter.model, parameter.typeValue, value
    )
    parameter.defaultValue = default_value
    if default_value is not None:
        default_value.owningParameter = parameter


def get_parameter_lower_value(parameter: Parameter) -> int | None:
    """Get lower value of a parameter."""
    if parameter.lowerValue is None:
        return None
    if isinstance(parameter.lowerValue, LiteralInteger):
        return int(parameter.lowerValue.value)
    return None


def get_parameter_lower_value_as_string(parameter: Parameter) -> str | None:
    """Get lower value of a parameter as a string."""
    if parameter.lowerValue is None:
        return None
    if isinstance(parameter.lowerValue, LiteralInteger):
        return str(parameter.lowerValue.value)
    return None


def set_parameter_lower_value(parameter: Parameter, value: int | None) -> None:
    """Set lower value of a parameter."""
    if parameter.lowerValue:
        parameter.lowerValue.unlink()
    if value is None:
        return
    lower_value = parameter.model.create(LiteralInteger)
    parameter.lowerValue = lower_value
    lower_value.owningLower = parameter
    parameter.lowerValue.value = value
    parameter.lowerValue.name = str(value)


def set_parameter_lower_value_from_string(
    parameter: Parameter, value: str | None
) -> None:
    """Set lower value of a parameter from a string."""
    if parameter.lowerValue:
        parameter.lowerValue.unlink()
    if value is None:
        return
    lower_value = parameter.model.create(LiteralInteger)
    parameter.lowerValue = lower_value
    lower_value.owningLower = parameter
    parameter.lowerValue.value = int(value)
    parameter.lowerValue.name = value


def get_parameter_upper_value(parameter: Parameter) -> UnlimitedNatural | None:
    """Get upper value of a parameter."""
    if parameter.upperValue is None:
        return None
    if isinstance(parameter.upperValue, LiteralUnlimitedNatural):
        return UnlimitedNatural(parameter.upperValue.value)
    return None


def get_parameter_upper_value_as_string(parameter: Parameter) -> str | None:
    """Get upper value of a parameter as a string."""
    if parameter.upperValue is None:
        return None
    if isinstance(parameter.upperValue, LiteralUnlimitedNatural):
        if math.isinf(parameter.upperValue.value):
            return "*"
        return str(int(parameter.upperValue.value))
    return None


def set_parameter_upper_value(
    parameter: Parameter, value: UnlimitedNatural | None
) -> None:
    """Set upper value of a parameter."""
    if parameter.upperValue:
        parameter.upperValue.unlink()
    if value is None:
        return
    upper_value = parameter.model.create(LiteralUnlimitedNatural)
    parameter.upperValue = upper_value
    upper_value.owningUpper = parameter
    parameter.upperValue.value = value
    if math.isinf(value):
        parameter.upperValue.name = "*"
    else:
        parameter.upperValue.name = str(int(value))


def set_parameter_upper_value_from_string(
    parameter: Parameter, value: str | None
) -> None:
    """Set upper value of a parameter from a string."""
    if parameter.upperValue:
        parameter.upperValue.unlink()
    if value is None:
        return
    upper_value = parameter.model.create(LiteralUnlimitedNatural)
    parameter.upperValue = upper_value
    upper_value.owningUpper = parameter
    if value == "*":
        parameter.upperValue.value = UnlimitedNatural(math.inf)
    else:
        parameter.upperValue.value = UnlimitedNatural(int(value))
    parameter.upperValue.name = value
