# Attribute Exploration by Sampling

Attribute Exploration is an algorithm through which we calculate a set of implications by querying an expert whether they hold or not. In the later case, we ask the expert to provide a counter-example that violates the implication he did not confirm.

This algorithm implements the very same idea to calculate functional dependencies in large datasets.
To achieve this, the expert is replaced by a program that has an efficient mechanism to verify whether an implications holds. It also can efficiently provide a counter-example when the implication does not hold.

The attribute exploration algorithms begins with an empty formal context, i.e. with attributes and no objects in which the implication {}->M holds (where M is the set of all attributes).
The "expert" has a partition pattern structure representation of the database which allows it to efficiently verify implications and search for counter-examples when implications do not hold.
