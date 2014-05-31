%define __strip /bin/true
%define _build_name_fmt    %%{ARCH}/%%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.vanish.rpm
# meta spec file for cross-chroot setup
#
# Copyright (c) 2009-2011 Martin Mohring   (martin.mohring@opensuse.org)
# Copyright (c) 2011      5eEcoSystems     (info@5eecosystems.com)
#
# All modifications and additions to the file contributed by third parties
# remain the property of the copyright owners, unless otherwise agreed
# upon. The cross build accelerators as is, and modifications
# and additions to the it, are licensed under the GPLv2.
# In addition, the cross build accelerators are licensed together with
# a package where they will be contained in
# under the license of the prestine package (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

#\/\/\/\/\/\/\/\/\/\/
### only changes here

#
# The original package name
%define oldname zlib

#
# The architectures this meta package is built on
%define myexclusive i586

#
# The required package for building this package
# This can be distribution dependent. Good start is:
# e.g. rpm grep tar sed patchelf
#
BuildRequires: rpm grep tar sed patchelf

#
# Additional required packages needed in addition to those of original package
# e.g. (usually empty) for an accelerator to be 100% compatible
#
#Requires:      <usuallyemptlylist>

# For a real accelerator, also the old packge is required for compatibility
# pls change this only if you know what you do
Requires:      %oldname

#
# Release under which to put the accelerator
# e.g. 1 or higher
#
Release:       8

### no changes needed below this line
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

### no changes needed
#
# The new package name - convention is %oldname-x86
%define newname %{oldname}-x86
#
# The version of the original package is read from its rpm db info
%{expand:%%define newversion %(rpm -q --qf '[%{version}]' %oldname)}
#
# The license of the original package is read from its rpm db info
%{expand:%%define newlicense %(rpm -q --qf '[%{license}]' %oldname)}
#
# The group information of the original package
%{expand:%%define newgroup %(rpm -q --qf '[%{group}]' %oldname)}
#
# The summary of the original package
%{expand:%%define newsummary %(rpm -q --qf '[%{summary} - special version ]' %oldname)}
#
# New rpath to add to files on request
%define newrpath "/emul/ia32-linux/lib:/emul/ia32-linux/usr/lib"
%define newinterpreter /emul/ia32-linux/lib/ld-linux.so.2
#
# Some automatic checks for availability
# binaries_to_prepare
%define binaries_to_prepare %{expand:%(test -e %{_sourcedir}/binaries_to_prepare && echo 1 || echo 0)}
%define libraries_to_prepare %{expand:%(test -e %{_sourcedir}/libraries_to_prepare && echo 1 || echo 0)}
%define special_script %{expand:%(test -e %{_sourcedir}/special_script && echo 1 || echo 0)}
%define files_to_ignore %{expand:%(test -e %{_sourcedir}/files_to_ignore && echo 1 || echo 0)}
#
### no changes needed below this line
%define nodebug 1


Name:          %newname
Version:       %newversion
AutoReqProv:   0
Provides:      %newname
BuildRequires: %oldname
# no auto requirements - they're generated
License:       %newlicense
Group:         %newgroup
ExclusiveArch: %myexclusive
Summary:       Dont use %newsummary !
BuildRoot:     %{_tmppath}/%{name}-%{version}-build
%if %binaries_to_prepare
Source10:      binaries_to_prepare
%endif
%if %libraries_to_prepare
Source20:      libraries_to_prepare
%endif
%if %special_script
Source30:      special_script
%endif
%if %files_to_ignore
Source40:      files_to_ignore
%endif
Source100:     baselibs.conf

%description
This is a meta-package providing %name.
It is not intended to be used on a normal system/device!
Original description:
%{expand:%(rpm -q --qf '[%{description}]' %oldname)}


%prep

%build

%install
%if %nodebug
set +x
%endif
mkdir -p %buildroot
rpm -ql %oldname > filestoinclude1

# ignore files - construct sed script
sedtmp="sedtmp.$$"
echo "s#^%{_docdir}.*##" >> $sedtmp
echo "s#^%{_mandir}.*##" >> $sedtmp
echo "s#^%{_infodir}.*##" >> $sedtmp

# evaluate files_to_ignore
%if %files_to_ignore
for i in `cat %{_sourcedir}/files_to_ignore`; do
 echo "Ignoring file: $i"
 echo "s#^${i}.*##" >> $sedtmp
done
%endif

# ignore default filesystem files
for i in `rpm -ql filesystem`; do
  echo "s#^${i}\$##" >> $sedtmp
done

#finish up
echo "/^\$/d" >> $sedtmp

#execute
sed -f $sedtmp -i filestoinclude1

# tar copy to buildroot
tar -T filestoinclude1 -cpf - | ( cd %buildroot && tar -xpf - )
rm filestoinclude1

# Todo: refractor
# no directories, in filelist
find %buildroot >  filestoinclude2
cat filestoinclude2 | sed -e "s#%{buildroot}##g" | uniq | sort > filestoinclude1
for i in `cat filestoinclude1`; do
# no directories
  if ! test -d %buildroot/$i ; then
    # 
    echo "$i" >> filestoinclude
  fi
done
rm filestoinclude1
rm filestoinclude2

# patchelf the binaries
%if %binaries_to_prepare
echo ""
echo "[ .oO Preparing binaries Oo. ]"
echo ""
mkdir -p %buildroot/%{_prefix}/share/applybinary/
for binary in `cat %{_sourcedir}/binaries_to_prepare` ; do
  echo "Processing binary: $binary"
  tmp="tmp.$$"
%if %nodebug
  debug=
%else
  debug="--debug"
%endif
  if file $binary | grep -q dynamic; then
    ldd $binary  | grep -v "ld-linux" | grep -v "linux-gate" |  sed -e "s#=.*##g" -e "s#^\t*##g"  > $tmp
    deps=$(for i in `cat $tmp` ; do rpm -q --whatprovides "$i" | grep -v "no package"; done)
    cleandeps=$(echo "$cleandeps" "$deps" | sort | uniq | sed -e "s/-[0-9].*//g")
    patchelf $debug --set-rpath %newrpath %buildroot/$binary
    patchelf $debug --set-interpreter %newinterpreter %buildroot/$binary
    patchelf $debug --set-rpath %newrpath %buildroot/$binary
    patchelf $debug --set-interpreter %newinterpreter %buildroot/$binary
    if test -n "$debug"; then
      patchelf --print-rpath %buildroot/$binary
      patchelf --print-interpreter %buildroot/$binary
    fi
  fi
  echo "$binary" >> %buildroot/%{_prefix}/share/applybinary/%name
  echo ""
done
%endif

# stub
%if %libraries_to_prepare
echo ""
echo "[ .oO Preparing libraries Oo. ]"
echo ""
%endif

# stub
%if %special_script
echo ""
echo "[ .oO Executing special script Oo. ]"
echo ""
%endif

# lets start the shellquote nightmare ;)
shellquote()
{
    for arg; do
        arg=${arg//\\/\\\\}
#        arg=${arg//\$/\$}   # already needs quoting ;(
#        arg=${arg/\"/\\\"}  # dito
#        arg=${arg//\`/\`}   # dito
        arg=${arg//\\|/\|}
        arg=${arg//\\|/|}
        echo "$arg"
    done
}


echo "Creating baselibs_new.conf"
echo ""
rm -rRf /tmp/baselibs_new.conf || true

shellquote "%{name}" >> /tmp/baselibs_new.conf
shellquote "  targettype x86 block!" >> /tmp/baselibs_new.conf
shellquote "  targettype 32bit block!" >> /tmp/baselibs_new.conf
shellquote "  targettype arm autoreqprov off" >> /tmp/baselibs_new.conf

# automagically fill in basic requirements
for i in $cleandeps ; do 
  shellquote "  targettype arm requires \"${i}-x86-arm\"" >> /tmp/baselibs_new.conf
done

# we require the native version
shellquote "  targettype arm requires \"%{oldname}\" " >> /tmp/baselibs_new.conf
shellquote "  targettype arm prefix /emul/ia32-linux" >> /tmp/baselibs_new.conf
shellquote "  targettype arm extension -arm" >> /tmp/baselibs_new.conf
shellquote "  targettype arm +/" >> /tmp/baselibs_new.conf

# safe space and download time
shellquote "  targettype arm -/%{_mandir}" >> /tmp/baselibs_new.conf
shellquote "  targettype arm -/%{_docdir}" >> /tmp/baselibs_new.conf
shellquote "  targettype arm requires \"tizen-accelerator\"" >> /tmp/baselibs_new.conf

# replace native with x86 binaries as defined in file
%if %binaries_to_prepare
# Todo: error handling if .orig-arm is present
for binary in `cat %{_sourcedir}/binaries_to_prepare` ; do
   shellquote "  targettype arm post \"  if test -e ${binary}.orig-arm -a -h ${binary}; then \" " >> /tmp/baselibs_new.conf
   shellquote "  targettype arm post \"    echo \"${binary}.orig-arm already present - skipping.\" \" " >> /tmp/baselibs_new.conf
   shellquote "  targettype arm post \"  else \" " >> /tmp/baselibs_new.conf
   shellquote "  targettype arm post \"    mv ${binary} ${binary}.orig-arm ; ln -s <prefix>${binary} ${binary} \"" >> /tmp/baselibs_new.conf
   shellquote "  targettype arm post \"  fi \" " >> /tmp/baselibs_new.conf
done

shellquote " " >> /tmp/baselibs_new.conf
for binary in `cat %{_sourcedir}/binaries_to_prepare` ; do

  shellquote "  targettype arm preun \"  if test -e ${binary}.orig-arm ; then \"" >> /tmp/baselibs_new.conf
  shellquote "  targettype arm preun \"    rm -f ${binary} ; mv ${binary}.orig-arm ${binary}\"" >> /tmp/baselibs_new.conf
  shellquote "  targettype arm preun \"  fi \"" >> /tmp/baselibs_new.conf

done
%endif

cat /tmp/baselibs_new.conf >> %{_sourcedir}/baselibs.conf

echo "################################################################################"
echo ""
echo ""
echo "REQUIREMENTS:"
grep "requires" %{_sourcedir}/baselibs.conf | sort | uniq | sed -e "s#  targettype.*requires ##g" | while read k ; do
 echo "CBinstall: $k"
done
echo "Runscripts: %{newname}-arm"
echo ""
echo ""
echo "################################################################################"
set -x

%clean
rm -rf $RPM_BUILD_ROOT

%files -f filestoinclude
%defattr(-,root,root)
%if %binaries_to_prepare
/%{_prefix}/share/applybinary/%name
%endif
