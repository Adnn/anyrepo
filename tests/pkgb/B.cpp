#include "B.h"

int fac(int a)
{
    if (a == 1)
    {
        return a;
    }

    return sum(a, fac(a-1));
}
