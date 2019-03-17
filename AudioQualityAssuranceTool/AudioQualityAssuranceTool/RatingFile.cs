using System;
using System.ComponentModel;
using System.IO;
using System.Runtime.CompilerServices;
using AudioQualityAssuranceTool.Annotations;
using CsvHelper.Configuration.Attributes;

namespace AudioQualityAssuranceTool
{
    public enum RatingStatus { BAD, GOOD, PERFECT }

    public class RatingFile : INotifyPropertyChanged
    {

        public event PropertyChangedEventHandler PropertyChanged;
        [NotifyPropertyChangedInvocator]
        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        [Ignore]
        public Guid Id { get; }

        public static string VocalsPrefix => "vocals_";

        public FileInfo File;

        public bool? Pass => Status > RatingStatus.BAD;


        private RatingStatus? _status;

        public RatingStatus? Status
        {
            get => _status;
            set
            {
                _status = value;
                OnPropertyChanged(nameof(Status));
            }
        }

        public string FileName => File?.Name ?? string.Empty;

        public string Collection => File?.Directory?.Parent?.Name ?? string.Empty;

        public string Prefix => FileName.Replace(VocalsPrefix, string.Empty).Substring(0, 1)?.ToUpper() ?? string.Empty;

        public RatingFile()
        {
            Id = Guid.NewGuid();
        }
    }

}
