#include <string.h>
#include<stdio.h>
int lengthOfLongestSubstring(char *s);
void main ()
{
  int a  = lengthOfLongestSubstring("helloworld");
}

int lengthOfLongestSubstring(char *s) {
   // for the all the possible charter
     int lastIndex[256];
    //setting them as -1
    for (int i = 0; i < 256; i++) lastIndex[i] = -1;

    int maxLen = 0;
    int left = 0;

    for (int right = 0; s[right] != '\0'; right++) {
        unsigned char c = s[right];

        if (lastIndex[c] >= left) {
            left = lastIndex[c] + 1; // move left pointer past the duplicate
        }

        lastIndex[c] = right; // update last seen index
        int windowLen = right - left + 1;
        if (windowLen > maxLen) maxLen = windowLen;
    }

    return maxLen;
}