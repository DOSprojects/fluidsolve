The ``core`` submodule
======================

The core module contains the ComponentBuilder class. Although is is perfectly possible to instanciate the components themselves, this is not the best practice.
The recommended way is the use of this builder class. One of the thisgs this builder does is providing a unique name to the component.
If this naming is not done correctly, then parts of this toolkit woll not work or give wrong results.

Main parts of the class are:
- Setting common conditions for the medium
- Component creation with a correct naming an medium

.. automodule:: fluidsolve.core
   :members:
   :undoc-members:
   :show-inheritance: