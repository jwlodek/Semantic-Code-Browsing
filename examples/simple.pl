parent(a, b).
male(a).
father(X, Y) :- parent(X, Y), male(X).