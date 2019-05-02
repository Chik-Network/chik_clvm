from opacity.int_keyword import from_int_keyword_tokens, to_int_keyword_tokens

from .ReduceError import ReduceError


def make_reduce_f(operator_lookup, quote_kw, reduce_kw, env_kw):

    def reduce_core(reduce_f, form, env):
        if not form.listp():
            raise ReduceError("%s is not a list" % form)

        if form.nullp():
            raise ReduceError("reduce_list cannot handle empty list")

        first_item = form.first()

        f_index = first_item.as_atom()
        if f_index is None:
            raise ReduceError("non-byte atom %s in first element of list" % first_item)

        # special form QUOTE

        if f_index == quote_kw:
            if form.rest().nullp() or not form.rest().rest().nullp():
                raise ReduceError("quote requires exactly 1 parameter, got %d" % (
                    len(list(form.as_iter())) - 1))
            return form.rest().first()

        # TODO: rewrite with cons, rest, etc.
        args = form.to([reduce_f(reduce_f, _, env) for _ in form.rest().as_iter()])

        # keyword REDUCE

        if f_index == reduce_kw:
            if args.rest().nullp() or not args.rest().rest().nullp():
                raise ReduceError("reduce_list requires 2 parameters, got %d" % len(list(args.as_iter())))
            return reduce_f(reduce_f, args.first(), args.rest().first())

        # keyword ENV

        if f_index == env_kw:
            if form.nullp() or not form.rest().nullp():
                raise ReduceError("env requires no parameters, got %d" % (list(args.as_iter())))
            return env

        # special form APPLY

        f = operator_lookup.get(f_index)
        if f:
            return f(args)

        raise ReduceError("unknown function index %s" % f_index)

    return reduce_core
